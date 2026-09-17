# Release process

Only tags are used by now (not releases).

Do not remove '# Connecting' in README.md.

# Tagging a release

If a version needs to be changed, edit `elm/__version__.py`.

This file is read by *setup.py*.

If the version is not changed, the publishing procedure works using the same version with a different build number.

The GITHUB_RUN_NUMBER environment variable, when available, is read by *setup.py*.

Push all changes:

```shell
git commit -a
git push
```

_After pushing the last commit_, add a local tag (shall be added AFTER the commit that needs to be published):

```shell
git tag # list local tags
git tag v0.1.4
```

Notes:

- correspondence between tag and `__version__.py` is not automatic.
- the tag must start with "v" if a GitHub Action workflow needs to be run

Push this tag to the origin, which starts the PyPI publishing workflow (GitHub Action):

```shell
git push origin v0.1.4
git ls-remote --tags https://github.com/Ircama/ELM327-emulator # list remote tags
```

Check the published tag here: https://github.com/Ircama/ELM327-emulator/tags

It shall be even with the last commit.

Check the GitHub Action: https://github.com/Ircama/ELM327-emulator/actions

Check PyPI:

- https://test.pypi.org/manage/project/ELM327-emulator/releases/
- https://pypi.org/manage/project/ELM327-emulator/releases/

End user publishing page:

- https://test.pypi.org/project/ELM327-emulator
- https://pypi.org/project/ELM327-emulator/

Verify whether wrong builds need to be removed.

Test installation:

```shell
cd
python3 -m pip uninstall -y ELM327-emulator
python3 -m pip install ELM327-emulator
elm
python3 -m pip uninstall -y ELM327-emulator
```

# Updating the same tag (using a different build number for publishing)

```shell
git tag # list tags
git tag -d v0.1.5 # remove local tag
git push --delete origin v0.1.5 # remove remote tag
git ls-remote --tags https://github.com/Ircama/ELM327-emulator # list remote tags
```

Then follow the tagging procedure again to add the tag to the latest commit.

# Testing the build procedure locally

The build backend is declared in `pyproject.toml` (`setuptools`), so that the
build works on Python 3.14 too: since Python 3.14 the build backend is no longer
implicitly available in the isolated build environment and the `pkg_resources`
module removed from recent setuptools is no longer used by `setup.py`.

```shell
cd <repository directory>
```

## Local build (using build):

```shell
python3 -m build --sdist --wheel --outdir dist/ .
python3 -m twine upload --repository testpypi dist/*
```

## Local build (using setup):

```shell
python3 setup.py sdist bdist_wheel
python3 -m twine upload --repository testpypi dist/*
```

## Local build (using build versions):

```shell
GITHUB_RUN_NUMBER=31 python3 setup.py sdist bdist_wheel
python3 -m twine upload --repository testpypi dist/*
```

## Removing directories

```shell
ls -l dist
rm -r build dist ELM327_emulator.egg-info
```

# Security notes

The TCP/IP interface (`-n`) binds its socket to the `127.0.0.1` loopback address
by default, so that the emulator (which implements no authentication) is not
exposed to other hosts. The interface can be changed with the `-i`/`--interface`
option; `-i 0.0.0.0` (or `-i ::`) restores the previous behaviour of accepting
connections from any address and produces a warning at startup. Mention this in
the release notes, because it changes the default behaviour of the `-n` option.
