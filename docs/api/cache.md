# Cache de numeros

## GET /api/numbers
Lista todos los numeros.

## GET /api/numbers/<phone>
Obtiene un numero.

## GET /api/numbers/<phone>/exists
Verifica existencia.

## POST /api/numbers
Crea o recrea un numero.

Body:
- phone (string, requerido)
- name (string, opcional)
- data (object, opcional)

## PATCH /api/numbers/<phone>
Actualiza un numero.

Body:
- data (object, requerido)

## PATCH /api/numbers/update
Actualiza un numero con phone en el body.

Body:
- phone (string, requerido)
- data (object, requerido)

## PATCH /api/numbers/bulk-update
Actualiza multiples numeros.

Body:
- phones (array, requerido)
- data (object, requerido)

## DELETE /api/numbers/<phone>
Elimina un numero.

## POST /api/numbers/clear
Limpia todos los numeros.
