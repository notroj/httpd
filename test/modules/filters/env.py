import inspect
import logging
import os

from pyhttpd.env import HttpdTestEnv, HttpdTestSetup

log = logging.getLogger(__name__)


class FiltersTestSetup(HttpdTestSetup):

    def __init__(self, env: 'HttpdTestEnv'):
        super().__init__(env=env)
        self.add_source_dir(os.path.dirname(inspect.getfile(FiltersTestSetup)))
        self.add_modules(["env"])
        # mod_proxy_html and mod_xml2enc need libxml2 at build time, so they
        # must not be a hard requirement; their tests skip when absent.
        self.add_optional_modules(["xml2enc", "proxy_html"])


class FiltersTestEnv(HttpdTestEnv):

    def __init__(self, pytestconfig=None):
        super().__init__(pytestconfig=pytestconfig)
        # A LogLevel for an unloaded module is a fatal config error, so only
        # raise it for mod_proxy_html when it was built.
        log_modules = ["core"]
        if self.has_proxy_html_module:
            log_modules.insert(0, "proxy_html")
        self.add_httpd_log_modules(log_modules)

    def setup_httpd(self, setup: HttpdTestSetup = None):
        super().setup_httpd(setup=FiltersTestSetup(env=self))

    @property
    def has_proxy_html_module(self) -> bool:
        """Whether mod_proxy_html was built."""
        return self.has_shared_module("proxy_html")
