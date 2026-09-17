import pytest

from pyhttpd.conf import HttpdConf

# mod_proxy_balancer keeps its member state in a slotmem segment, and with
# BalancerPersist it writes that segment to disk and reads it back on the next
# start.  That exercises the layout-size arithmetic in the slotmem providers
# from both ends: the size used to create and store the segment, and the size
# slotmem_attach() expects to find.


class TestBalancerSlotmem:

    @pytest.fixture(autouse=True, scope='class')
    def _class_scope(self, env):
        conf = HttpdConf(env)
        conf.add("ProxyPreserveHost on")
        conf.add("BalancerPersist On")
        conf.start_vhost(domains=[env.d_reverse], port=env.https_port)
        conf.add([
            "<Proxy \"balancer://slotmemtest\">",
            f"    BalancerMember \"http://127.0.0.1:{env.http_port}\"",
            "</Proxy>",
            "ProxyPass \"/\" \"balancer://slotmemtest/\"",
        ])
        conf.end_vhost()
        conf.add_vhost(domains=[env.d_reverse], port=env.http_port,
                       doc_root='htdocs/test1')
        conf.install()
        assert env.apache_restart() == 0

    def get(self, env):
        return env.curl_get(
            f"https://{env.d_reverse}:{env.https_port}/alive.json", 5)

    # The balancer works on the run that creates the slotmem segment.
    def test_proxy_07_01(self, env):
        r = self.get(env)
        assert r.response, f"no response: {r.stderr}"
        assert r.response["status"] == 200

    # ...and still works after a restart, which persists the segment and
    # attaches to it again with the size the provider computes.
    def test_proxy_07_02(self, env):
        assert env.apache_restart() == 0
        r = self.get(env)
        assert r.response, f"no response after restart: {r.stderr}"
        assert r.response["status"] == 200

    # A second restart, so the attach path runs against a segment that was
    # itself restored rather than freshly created.
    def test_proxy_07_03(self, env):
        assert env.apache_restart() == 0
        r = self.get(env)
        assert r.response, f"no response after 2nd restart: {r.stderr}"
        assert r.response["status"] == 200
