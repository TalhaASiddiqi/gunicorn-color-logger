"""Custom Gunicorn access logger with rich color support."""

VERSION = (0, 1, 0)  # PEP 386  # noqa
__version__ = ".".join([str(x) for x in VERSION])  # noqa

import datetime
import logging
import traceback
from rich.logging import RichHandler, get_console
from rich.console import LogRender, Text

from gunicorn.glogging import Logger as GunicornBaseLogger


__all__ = (
    "Logger",
    "AiohttpLogger",
)

class Logger(GunicornBaseLogger):
    """Custom gunicorn logger with rich capabilities."""
    
    CODE_COLOR_MAPPING = {
        '1': 'yellow',
        '2': 'green',
        '3': 'cyan',
        '4': 'magenta',
        '5': 'red',
    }
    
    LOG_FORMAT = '%(m)s %(U)s?%(q)s (%(L)s s) "%(f)s"'
    
    def __init__(self, *args, **kwargs):
        self.console = get_console()
        super().__init__(*args, **kwargs)
        
        self.log_render = LogRender(
            show_time=True,
            show_level=True,
            show_path=False,
            time_format="[%X]",
            omit_repeated_times=True,
            level_width=None,
        )
        
        
    def colorize_atoms(self, atoms):
        """Colorize separate atoms.
        """
        
        def wrap_with_color(key, color, attrs=None):
            """Wrap atom with color."""
            attr_string = " " + " ".join(attrs) if attrs else ""
            atoms[key] = f"[{color + attr_string}]{atoms[key]}[/]"
        
        wrap_with_color('U', 'cyan')
        wrap_with_color('q', 'cyan')
        wrap_with_color('m', 'blue', attrs=['bold'])
        if float(atoms['L']) > 1:
            wrap_with_color('L', 'red bold')
        
        return atoms

    def access(self, resp, req, environ, request_time):
        """Write access log entry.
        """
        if not (self.cfg.accesslog or self.cfg.logconfig or self.cfg.syslog):
            return
        
        atoms = self.atoms(resp, req, environ, request_time)
        # wrap atoms:
        # - make sure atoms will be tested properly
        # - if atom doesn't exist replace it by '-'
        safe_atoms = self.atoms_wrapper_class(atoms)
        safe_atoms = self.colorize_atoms(safe_atoms)
        
        message_renderable = Text.from_markup(self.LOG_FORMAT % safe_atoms)
        
        (status_color) = self.CODE_COLOR_MAPPING.setdefault(atoms['s'][0], "")
        
        status = Text(atoms['s'], style=f"bold {status_color}")
        
        rendered = self.log_render(
            self.console,
            [message_renderable],
            log_time=datetime.datetime.now(),
            time_format="[%X]",
            level=status,
            path=None,
            line_no=None,
            link_path=None,
        )
        
        try:
            self.console.print(rendered)
        except:
            self.error(traceback.format_exc())
    
    def _set_handler(self, log, output, fmt, stream=None):
        if log == self.error_log or log == self.access_log:
            # remove previous gunicorn log handler
            h = self._get_gunicorn_handler(log)
            if h:
                log.handlers.remove(h)
            
            formatter = logging.Formatter(fmt='%(message)s')
            h = RichHandler(console=self.console, rich_tracebacks=True, log_time_format="[%X]", show_path=log == self.error_log)
            h._gunicorn = True
            h.setFormatter(formatter)
            log.addHandler(h)
            
            return
            
        super()._set_handler(log, output, fmt, stream)


