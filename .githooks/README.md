# Git hooks

<!-- HUELLA-PORTAFOLIO-HOOK-DOC-RATIFIED-20261031 -->

Activa los hooks versionados en este clon con:

```sh
 git config core.hooksPath .githooks
```

El hook `pre-push` ejecuta `tests/test_portafolio_contacto.sh`. Comprueba los dos HTML locales y consulta las dos páginas publicadas; por tanto, requiere red y que GitHub Pages responda HTTP 200.

Para una sola operación, sin guardar la configuración local:

```sh
 git -c core.hooksPath=.githooks push
```
