#! /bin/sh

# Tag tree and update version number in change log and
# in setup.py before building.

REPO=debian-repo
COMPONENT=main
KEYID=03C3951A  # Autobuild keyid
DEB_DIST="sid wheezy squeeze quantal precise oneiric natty raring"
DEB_BUILD=$(lsb_release -s -c)

if [ ! -d debian ] ; then
    echo "Are we in the right directory"
    exit 1
fi

if gpg --list-keys 2>/dev/null | grep -q ${KEYID} ; then
    echo "Signing packages and repo with ${KEYID}"
else
    echo "Package signing key (${KEYID}) not found"
    echo "Have you set $GNUPGHOME ? "
    exit 3
fi

# Build Package
echo "Building for dist: $DEB_BUILD"
dpkg-buildpackage -k$KEYID
if [ $? -ne 0 ] ; then
    echo "Build failed"
    exit 2
fi

# Build Repo
PKG=../ceph-deploy*.changes
mkdir -p $REPO/conf
if [ -e $REPO/conf/distributions ] ; then
    rm -f $REPO/conf/distributions
fi

for DIST in  $DEB_DIST ; do
    cat <<EOF >> $REPO/conf/distributions
Codename: $DIST
Suite: stable
Components: $COMPONENT
Architectures: i386 amd64 source
Origin: Inktank
Description: Ceph distributed file system
DebIndices: Packages Release . .gz .bz2
DscIndices: Sources Release .gz .bz2
Contents: .gz .bz2
SignWith: $KEYID

EOF
done

echo "Adding package to repo, dist: $DEB_BUILD"
reprepro --ask-passphrase -b $REPO -C $COMPONENT --ignore=undefinedtarget --ignore=wrongdistribution include $DEB_BUILD $PKG

for DIST in $DEB_DIST
do
    [ "$DIST" = "$DEB_BUILD" ] && continue
    echo "Copying package to dist: $DIST"
    reprepro -b $REPO --ignore=undefinedtarget --ignore=wrongdistribution copy $DIST $DEB_BUILD ceph-deploy
done

echo "Done"
