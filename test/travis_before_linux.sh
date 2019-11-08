#!/bin/bash -ex
if ! test -v SKIP_TESTING; then
   svn export -q https://svn.apache.org/repos/asf/httpd/test/framework/trunk test/perl-framework
fi
if test -v APR_VERSION; then
    trunk_url=https://svn.apache.org/repos/asf/apr/apr/trunk
    # If there is an APR trunk install cached in ~/root/apr-trunk,
    # blow it away and rebuild it if the revision it was built from
    # has changed.
    if test $APR_VERSION = trunk; then
        trunk_rev=`svn info --show-item last-changed-revision ${trunk_url}`
        test -f $HOME/root/apr-trunk/.revision-is-${trunk_rev} || rm -rf $HOME/root/apr-trunk*
    fi
    if ! test -d $HOME/root/apr-${APR_VERSION}; then
        case $APR_VERSION in
            trunk) svn export -r ${trunk_rev} ${trunk_url} $HOME/build/apr-trunk
                   touch $HOME/root/apr-trunk/.revision-is-${trunk_rev} ;;
            *) svn export -q https://svn.apache.org/repos/asf/apr/apr/tags/${APR_VERSION} \
                   $HOME/build/apr-${APR_VERSION} ;;
        esac
        pushd $HOME/build/apr-${APR_VERSION}
        if [ $APR_VERSION = 1.4.1 ]; then
            # 1.4.1 doesn't build with current libtool
            svn cat https://svn.apache.org/repos/asf/apr/apr/tags/1.5.1/buildconf > buildconf
        fi
        ./buildconf
        ./configure ${APR_CONFIG} --prefix=$HOME/root/apr-${APR_VERSION}
        make -j2
        make install
        popd
        APU_CONFIG="$APU_CONFIG --with-apr=$HOME/root/apr-${APR_VERSION}"
    fi
fi
if test -v APU_VERSION; then
    if ! test -d $HOME/root/apu-${APU_VERSION}; then
        case $APU_VERSION in
            trunk) url=https://svn.apache.org/repos/asf/apr/apr-util/trunk ;;
            *) url=https://svn.apache.org/repos/asf/apr/apr-util/tags/${APU_VERSION} ;;
        esac
        svn export -q ${url} $HOME/build/apu-${APU_VERSION}
        pushd $HOME/build/apu-${APU_VERSION}
        ./buildconf --with-apr=$HOME/build/apr-${APR_VERSION}
        ./configure ${APU_CONFIG} --prefix=$HOME/root/apu-${APU_VERSION}
        make -j2
        make install
        popd
    fi
fi
