#! /bin/sh

# Tag tree and update version number in change log and
# in setup.py before building.

REPO=rpm-repo
KEYID=${KEYID:-03C3951A}  # Default is autobuild-key
BUILDAREA=./rpmbuild
DIST=el6
RPM_BUILD=$(lsb_release -s -c)

if [ ! -e setup.py ] ; then
    echo "Are we in the right directory"
    exit 1
fi

if gpg --list-keys 2>/dev/null | grep -q ${KEYID} ; then
    echo "Signing packages and repo with ${KEYID}"
else
    echo "Package signing key (${KEYID}) not found"
    echo "Have you set \$GNUPGHOME ? "
    exit 3
fi

if ! CREATEREPO=`which createrepo` ; then
    echo "Please install the createrepo package"
    exit 4
fi

# Create Tarball
python setup.py sdist --formats=bztar

# Build RPM
mkdir -p rpmbuild/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}
BUILDAREA=`readlink -fn ${BUILDAREA}`   ### rpm wants absolute path
cp ceph-deploy.spec ${BUILDAREA}/SPECS
cp dist/*.tar.bz2 ${BUILDAREA}/SOURCES
echo "buildarea is: ${BUILDAREA}"
rpmbuild -ba --define "_topdir ${BUILDAREA}" --define "_unpackaged_files_terminate_build 0" ${BUILDAREA}/SPECS/ceph-deploy.spec

# create repo
DEST=${REPO}/${DIST}
mkdir -p ${REPO}/${DIST}
cp -r ${BUILDAREA}/*RPMS ${DEST}

# Sign all the RPMs for this release
rpm_list=`find ${REPO} -name "*.rpm" -print`
rpm --addsign --define "_gpg_name ${KEYID}" $rpm_list

# Construct repodata
for dir in ${DEST}/SRPMS ${DEST}/RPMS/*
do
    if [ -d $dir ] ; then
        createrepo $dir
        gpg --detach-sign --armor -u ${KEYID} $dir/repodata/repomd.xml
    fi
done

exit 0
