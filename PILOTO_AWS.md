# Piloto FinOps AWS read-only

Diagnóstico acotado a una cuenta AWS, un período mensual y `us-east-1`. El acceso usa un rol de lectura; Platino Labs no modifica ni elimina recursos.

> **La muestra no es un cliente.** El [PDF de ejemplo](./finops-ejemplo-sintetico.pdf) usa una cuenta y recursos inventados. No demuestra resultados comerciales ni ahorros reales. La plantilla y el informe son materiales informativos; el convenio firmado define el alcance y el tratamiento de datos.

## Onboarding en tres pasos

1. **Acordar antes de desplegar.** Solicita el piloto por el [canal de contacto público](https://alexisromtz-lab.github.io/la-auditora/#contacto-titulo). Confirmamos alcance, ventana y tratamiento de archivos; cliente y Platino Labs firman el convenio antes de crear el rol. El precio de referencia es **USD 500** para el alcance indicado, sujeto a cotización y convenio. No hay enlace de pago en este documento. Después de acordar, Platino Labs entrega por un canal privado el ARN exacto del principal y un `ExternalId` único para ese rol.
2. **Desplegar el rol de lectura.** Descarga la [plantilla CloudFormation](./PLANTILLA_CFN_PLATINO_AUDIT_ROLE.yaml) y despliega la plantilla en la cuenta AWS del cliente. Completa únicamente `PrincipalPlatinoArn` y `ExternalId` con los valores entregados por Platino Labs. La plantilla limita las lecturas regionales a `us-east-1`; Cost Explorer se consulta en su región fija. Revisa la plantilla y los permisos antes de desplegar. No uses la raíz de la cuenta, comodines en el principal, access keys ni credenciales de consola.
3. **Verificar y entregar.** Comparte únicamente el `RoleArn` generado mediante el canal privado acordado, nunca en issues, pull requests o repositorios públicos. Platino Labs ya conoce el `ExternalId` que entregó; no hace falta reenviarlo. Tras validar el acceso, el plazo de entrega se acuerda por escrito antes de iniciar el análisis; esta guía no fija un SLA. El cliente puede revocar el acceso eliminando el rol o retirando el principal de confianza.

## Alcance y límites

- Se leen costos y cobertura de compromisos, inventario regional EC2/RDS y métricas CPU de EC2 conforme a la política de la plantilla. No se leen datos de aplicaciones, secretos, contenido de bases ni logs.
- Una región no equivale a un inventario global. Cualquier ampliación requiere acordar y validar el nuevo alcance.
- El diagnóstico no ejecuta recomendaciones ni garantiza ahorros futuros. Las proyecciones son aritméticas sobre datos del período medido.
- El precio, el criterio de garantía y el tratamiento/borrado de archivos quedan definidos en la propuesta y el convenio firmados; esta guía no los sustituye.

<!-- HUELLA-PILOTO-AWS-20261031 -->
<!-- HUELLA-PILOTO-EXTERNALID-20261031 -->
<!-- HUELLA-PILOTO-PLAZO-ACORDADO-20261031 -->
