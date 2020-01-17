# Public-inbox v2 extract utility

This script can be used to extract messages from a public-inbox v2 repository. This is helpful if you want to process the messages through your own tools (notmuch, for instance), rather than depending on public-inbox. This script has been used (and hence tested) only with the mailing lists hosted at [https://lore.kernel.org](https://lore.kernel.org/lists.html) (also mirrored at [https://git.kernel.org](https://git.kernel.org/pub/scm/public-inbox/)).

Steps:
- Clone one of the repositories:

```
	mkdir -p pi/linuxppc-dev/git
	git clone --mirror git://git.kernel.org/pub/scm/public-inbox/lists.ozlabs.org/linuxppc-dev/0.git pi/linuxppc-dev/git/0.git
```

- Extract it:

```
	mkdir -p ml/linuxppc-dev/0
	piv2_extract pi/linuxppc-dev/git/0.git ml/linuxppc-dev/0/
```

- Subsequently, the same command can be used to fetch the latest messages and to extract them.
