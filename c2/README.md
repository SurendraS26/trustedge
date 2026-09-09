![SWTPM Docker Arch Logo](etc/banner.png)

SWTPM Docker Arch
=================

A ready-to-use Docker image for [**SWTPM**](https://github.com/stefanberger/swtpm), a software-based TPM 2.0 emulator, built on Arch Linux and installed directly from the official pacman repositories.


Usage
-----

Installing SWTPM-Docker-Arch
```sh
git clone https://github.com/SurendraS26/swtpm-arch-docker.git
cd swtpm-arch-docker
docker build -t swtpm-arch -f Dockerfile .
docker run -p 127.0.0.1:2321-2322:2321-2322 swtpm-arch 
```
>Note : Don't miss the dot in the above command.

Connect using [`tpm2-tools`](https://github.com/tpm2-software/tpm2-tools):

```sh
tpm2_startup -T swtpm:host=127.0.0.1,port=2321 -c
tpm2_pcrread --tcti="swtpm:host=127.0.0.1,port=2321" sha256
```

TCTI configuration for TSS2:
```
swtpm:host=127.0.0.1,port=2321
```


Requirements
------------

- Docker
- `tpm2-tools` on the host


Acknowledgement
----------------

This image bundles [**SWTPM**](https://github.com/stefanberger/swtpm) and [**libtpms**](https://github.com/stefanberger/libtpms) (IBM Corporation, 3-Clause BSD), and is built on [**Arch Linux**](https://archlinux.org/), whose components carry their own respective open-source licenses.


License
-------

```
This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <https://unlicense.org>
```
