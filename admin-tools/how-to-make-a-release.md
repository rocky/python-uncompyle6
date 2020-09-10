<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-refresh-toc -->
**Table of Contents**

- [Get latest sources:](#get-latest-sources)
- [Change version in uncompyle6/version.py:](#change-version-in-uncompyle6versionpy)
- [Update ChangeLog:](#update-changelog)
- [Update NEWS.md from ChangeLog:](#update-newsmd-from-changelog)
- [Make sure pyenv is running and check newer versions](#make-sure-pyenv-is-running-and-check-newer-versions)
- [Switch to python-2.4, sync that up and build that first since it creates a tarball which we don't want.](#switch-to-python-24-sync-that-up-and-build-that-first-since-it-creates-a-tarball-which-we-dont-want)
- [Check against older versions](#check-against-older-versions)
- [Make packages and tag](#make-packages-and-tag)
- [Check package on github](#check-package-on-github)
- [Release on Github](#release-on-github)
- [Get onto PyPI](#get-onto-pypi)
- [Update tags:](#update-tags)

<!-- markdown-toc end -->
# Get latest sources:

    git pull

# Change version in uncompyle6/version.py:

    $ emacs uncompyle6/version.py
    $ source uncompyle6/version.py
    $ echo $VERSION
    $ git commit -m"Get ready for release $VERSION" .

# Update ChangeLog:

    $ make ChangeLog

#  Update NEWS.md from ChangeLog:

    $ emacs NEWS.md
    $ make check
    $ git commit --amend .
    $ git push   # get CI testing going early

# Make sure pyenv is running and check newer versions

    $ admin-tools/check-newer-versions.sh

# Switch to python-2.4, sync that up and build that first since it creates a tarball which we don't want.

    $ source admin-tools/setup-python-2.4.sh
    $ git merge master
	# Add and fix merge conflicts
	$ git commit

# Check against older versions

    $ admin-tools/check-older-versions.sh

# Make packages and tag

    $ . ./admin-tools/make-dist-older.sh
	$ pyenv local 3.8.5
	$ twine check dist/uncompyle6-$VERSION*
    $ git tag release-python-2.4-$VERSION
    $ ./admin-tools/make-dist-newer.sh
	$ twine check dist/uncompyle6-$VERSION*

# Check package on github

	$ [[ ! -d /tmp/gittest ]] && mkdir /tmp/gittest; pushd /tmp/gittest
	$ pyenv local 3.8.3
	$ pip install -e git://github.com/rocky/python-uncompyle6.git#egg=uncompyle6
	$ uncompyle6 --help
	$ pip uninstall uncompyle6
	$ popd

# Release on Github

Goto https://github.com/rocky/python-uncompyle6/releases

Now check the *tagged* release. (Checking the untagged release was previously done).

Todo: turn this into a script in `admin-tools`

	$ pushd /tmp/gittest
	$ pip install -e git://github.com/rocky/python-uncompyle6.git@$VERSION#egg=uncompyle6
	$ uncompyle6 --help
	$ pip uninstall uncompyle6
	$ popd


# Get onto PyPI

    $ twine upload dist/uncompyle6-${VERSION}*


# Update tags:

    $ git push --tags
    $ git pull --tags

# Move dist files to uploaded

	$ mv -v dist/uncompyle6-${VERSION}* dist/uploaded
