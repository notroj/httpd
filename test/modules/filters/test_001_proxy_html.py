import os

import pytest

from pyhttpd.conf import HttpdConf

# ProxyHTMLURLMap interpolates environment variables into the to-pattern when
# the V flag is given and ProxyHTMLInterp is on.  The documented syntax was
# ${var}, but httpd's own config parser expands ${...} first and warns
# AH00111 when the name is neither a Define nor a pre-start environment
# variable -- which a per-request variable never is.  %{ENV:var} is left alone
# by the config parser.
URLMAPS = """
    ProxyHTMLLinks a href
    <Location "/">
        SetOutputFilter proxy-html
        ProxyHTMLInterp On
        SetEnv PROXY_HTML_FORCE 1
        SetEnv PHTML_NEW newvalue
        SetEnv PHTML_OLD oldvalue
        ProxyHTMLURLMap /from/ /to/%{ENV:PHTML_NEW}/ V
        ProxyHTMLURLMap /old/ /to/${PHTML_OLD}/ V
    </Location>
    """


class TestProxyHtmlInterp:

    @pytest.fixture(autouse=True, scope='class')
    def _class_scope(self, env):
        if not env.has_proxy_html_module:
            pytest.skip("mod_proxy_html is not built")
        doc_dir = os.path.join(env.server_dir, "htdocs", "test1")
        with open(os.path.join(doc_dir, "links.html"), "w") as f:
            f.write('<html><body>\n'
                    '<a href="/from/page.html">new</a>\n'
                    '<a href="/old/page.html">old</a>\n'
                    '</body></html>\n')
        # The ${PHTML_OLD} above is expanded by the config parser before
        # mod_proxy_html ever sees it, which logs AH00111 at startup.
        env.httpd_error_log.add_ignored_lognos(["AH00111"])
        conf = HttpdConf(env, extras={
            f"test1.{env.http_tld}": URLMAPS,
        })
        conf.add_vhost_test1()
        conf.install()
        assert env.apache_restart() == 0

    def get_links(self, env):
        r = env.curl_get(env.mkurl("http", "test1", "/links.html"))
        assert r.response, f"no response: {r.stderr}"
        assert r.response["status"] == 200
        return r.response["body"].decode()

    # %{ENV:var} in the to-pattern is interpolated.
    def test_filters_001_01(self, env):
        body = self.get_links(env)
        assert '/to/newvalue/page.html' in body, \
            f"%{{ENV:PHTML_NEW}} not interpolated: {body}"

    # The old ${var} syntax keeps working.
    def test_filters_001_02(self, env):
        body = self.get_links(env)
        assert '/to/oldvalue/page.html' in body, \
            f"${{PHTML_OLD}} not interpolated: {body}"
