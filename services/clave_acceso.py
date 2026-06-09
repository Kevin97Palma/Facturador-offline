import random


CODIGOS_DOCUMENTO = {
    'factura': '01',
    'liquidacion': '03',
    'nota_credito': '04',
    'nota_debito': '05',
    'guia_remision': '06',
    'retencion': '07',
}


def generar_digito_verificador(clave_48: str) -> str:
    factores = [2, 3, 4, 5, 6, 7]
    suma = 0
    factor_idx = 0
    for digito in reversed(clave_48):
        suma += int(digito) * factores[factor_idx % 6]
        factor_idx += 1
    residuo = suma % 11
    if residuo == 0:
        return '0'
    elif residuo == 1:
        return '1'
    else:
        return str(11 - residuo)


def generar_clave_acceso(fecha, tipo_documento: str, ruc: str, ambiente: int,
                         establecimiento: str, punto_emision: str,
                         secuencial: int, codigo_numerico: str = None) -> str:
    if codigo_numerico is None:
        codigo_numerico = str(random.randint(10000000, 99999999))

    fecha_str = fecha.strftime('%d%m%Y')
    cod_doc = CODIGOS_DOCUMENTO.get(tipo_documento, tipo_documento)
    serie = f"{establecimiento}{punto_emision}"
    num_comprobante = str(secuencial).zfill(9)
    tipo_emision = '1'

    clave_48 = (
        fecha_str +
        cod_doc +
        ruc +
        str(ambiente) +
        serie +
        num_comprobante +
        codigo_numerico +
        tipo_emision
    )

    if len(clave_48) != 48:
        raise ValueError(f"Clave de 48 dígitos inválida: longitud {len(clave_48)}")

    digito = generar_digito_verificador(clave_48)
    return clave_48 + digito
