from datetime import date


def _escape(valor) -> str:
    if valor is None:
        return ''
    s = str(valor)
    s = s.replace('&', '&amp;')
    s = s.replace('<', '&lt;')
    s = s.replace('>', '&gt;')
    s = s.replace('"', '&quot;')
    s = s.replace("'", '&apos;')
    return s


def _fmt_fecha(d) -> str:
    if isinstance(d, str):
        return d
    return d.strftime('%d/%m/%Y')


def _info_tributaria(empresa, cod_doc: str, clave_acceso: str,
                     establecimiento: str, punto_emision: str,
                     secuencial: int) -> str:
    nombre_comercial = (
        f'<nombreComercial>{_escape(empresa.nombre_comercial)}</nombreComercial>'
        if empresa.nombre_comercial else ''
    )
    agente_ret = '<agenteRetencion>1</agenteRetencion>' if empresa.agente_retencion else ''
    regimen = (
        f'<contribuyenteRimpe>{_escape(empresa.texto_regimen)}</contribuyenteRimpe>'
        if empresa.contribuyente_rimpe else ''
    )
    return (
        f'<infoTributaria>'
        f'<ambiente>{empresa.ambiente}</ambiente>'
        f'<tipoEmision>1</tipoEmision>'
        f'<razonSocial>{_escape(empresa.razon_social)}</razonSocial>'
        f'{nombre_comercial}'
        f'<ruc>{empresa.ruc}</ruc>'
        f'<claveAcceso>{clave_acceso}</claveAcceso>'
        f'<codDoc>{cod_doc}</codDoc>'
        f'<estab>{establecimiento}</estab>'
        f'<ptoEmi>{punto_emision}</ptoEmi>'
        f'<secuencial>{str(secuencial).zfill(9)}</secuencial>'
        f'<dirMatriz>{_escape(empresa.direccion)}</dirMatriz>'
        f'{agente_ret}'
        f'{regimen}'
        f'</infoTributaria>'
    )


def generar_xml_factura(empresa, cliente, factura, detalles) -> str:
    contrib_especial = (
        f'<contribuyenteEspecial>{_escape(empresa.num_resolucion_contrib_especial)}</contribuyenteEspecial>'
        if empresa.contribuyente_especial else ''
    )
    obligado = 'SI' if empresa.obligado_contabilidad else 'NO'
    total_sin = float(factura.subtotal_sin_impuesto or 0)

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<factura id="comprobante" version="1.1.0">'
    )
    xml += _info_tributaria(empresa, '01', factura.clave_acceso,
                            empresa.establecimiento, empresa.punto_emision,
                            factura.numero)
    xml += (
        f'<infoFactura>'
        f'<fechaEmision>{_fmt_fecha(factura.fecha_emision)}</fechaEmision>'
        f'<dirEstablecimiento>{_escape(empresa.direccion)}</dirEstablecimiento>'
        f'{contrib_especial}'
        f'<obligadoContabilidad>{obligado}</obligadoContabilidad>'
        f'<tipoIdentificacionComprador>{cliente.tipo_identificacion}</tipoIdentificacionComprador>'
        f'<razonSocialComprador>{_escape(cliente.razon_social)}</razonSocialComprador>'
        f'<identificacionComprador>{cliente.identificacion}</identificacionComprador>'
        f'<direccionComprador>{_escape(cliente.direccion or "")}</direccionComprador>'
        f'<totalSinImpuestos>{total_sin:.2f}</totalSinImpuestos>'
        f'<totalDescuento>{float(factura.descuento_total or 0):.2f}</totalDescuento>'
    )

    xml += '<totalConImpuestos>'
    if float(factura.subtotal_iva_0 or 0) > 0:
        xml += (
            f'<totalImpuesto>'
            f'<codigo>2</codigo><codigoPorcentaje>0</codigoPorcentaje>'
            f'<baseImponible>{float(factura.subtotal_iva_0):.2f}</baseImponible>'
            f'<valor>0.00</valor>'
            f'</totalImpuesto>'
        )
    if float(factura.subtotal_iva_5 or 0) > 0:
        xml += (
            f'<totalImpuesto>'
            f'<codigo>2</codigo><codigoPorcentaje>5</codigoPorcentaje>'
            f'<baseImponible>{float(factura.subtotal_iva_5):.2f}</baseImponible>'
            f'<valor>{float(factura.iva_5 or 0):.2f}</valor>'
            f'</totalImpuesto>'
        )
    if float(factura.subtotal_iva_12 or 0) > 0:
        xml += (
            f'<totalImpuesto>'
            f'<codigo>2</codigo><codigoPorcentaje>2</codigoPorcentaje>'
            f'<baseImponible>{float(factura.subtotal_iva_12):.2f}</baseImponible>'
            f'<valor>{float(factura.iva_12 or 0):.2f}</valor>'
            f'</totalImpuesto>'
        )
    if float(factura.subtotal_iva_15 or 0) > 0:
        xml += (
            f'<totalImpuesto>'
            f'<codigo>2</codigo><codigoPorcentaje>4</codigoPorcentaje>'
            f'<baseImponible>{float(factura.subtotal_iva_15):.2f}</baseImponible>'
            f'<valor>{float(factura.iva_15 or 0):.2f}</valor>'
            f'</totalImpuesto>'
        )
    xml += '</totalConImpuestos>'

    xml += (
        f'<propina>0.00</propina>'
        f'<importeTotal>{float(factura.total or 0):.2f}</importeTotal>'
        f'<moneda>DOLAR</moneda>'
        f'<pagos>'
        f'<pago>'
        f'<formaPago>{factura.forma_pago or "01"}</formaPago>'
        f'<total>{float(factura.total or 0):.2f}</total>'
        f'</pago>'
        f'</pagos>'
        f'</infoFactura>'
    )

    xml += '<detalles>'
    for det in detalles:
        xml += (
            f'<detalle>'
            f'<codigoPrincipal>{_escape(det.codigo_principal or "")}</codigoPrincipal>'
            f'<descripcion>{_escape(det.descripcion)}</descripcion>'
            f'<cantidad>{float(det.cantidad):.4f}</cantidad>'
            f'<precioUnitario>{float(det.precio_unitario):.4f}</precioUnitario>'
            f'<descuento>{float(det.descuento or 0):.2f}</descuento>'
            f'<precioTotalSinImpuesto>{float(det.precio_total_sin_impuesto):.2f}</precioTotalSinImpuesto>'
            f'<impuestos>'
            f'<impuesto>'
            f'<codigo>{det.impuesto_codigo or "2"}</codigo>'
            f'<codigoPorcentaje>{det.impuesto_codigo_porcentaje or "0"}</codigoPorcentaje>'
            f'<tarifa>{float(det.impuesto_tarifa or 0):.2f}</tarifa>'
            f'<baseImponible>{float(det.precio_total_sin_impuesto):.2f}</baseImponible>'
            f'<valor>{float(det.impuesto_valor or 0):.2f}</valor>'
            f'</impuesto>'
            f'</impuestos>'
            f'</detalle>'
        )
    xml += '</detalles>'

    if cliente.email:
        xml += (
            f'<infoAdicional>'
            f'<campoAdicional nombre="Email">{_escape(cliente.email)}</campoAdicional>'
            f'</infoAdicional>'
        )

    xml += '</factura>'
    return xml


def generar_xml_retencion(empresa, proveedor, retencion, detalles) -> str:
    obligado = 'SI' if empresa.obligado_contabilidad else 'NO'
    contrib_especial = (
        f'<contribuyenteEspecial>{_escape(empresa.num_resolucion_contrib_especial)}</contribuyenteEspecial>'
        if empresa.contribuyente_especial else ''
    )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<comprobanteRetencion id="comprobante" version="2.0.0">'
    )
    xml += _info_tributaria(empresa, '07', retencion.clave_acceso,
                            empresa.establecimiento, empresa.punto_emision,
                            retencion.numero)
    xml += (
        f'<infoCompRetencion>'
        f'<fechaEmision>{_fmt_fecha(retencion.fecha_emision)}</fechaEmision>'
        f'<dirEstablecimiento>{_escape(empresa.direccion)}</dirEstablecimiento>'
        f'{contrib_especial}'
        f'<obligadoContabilidad>{obligado}</obligadoContabilidad>'
        f'<tipoIdentificacionSujetoRetenido>{proveedor.tipo_identificacion}</tipoIdentificacionSujetoRetenido>'
        f'<parteRel>NO</parteRel>'
        f'<razonSocialSujetoRetenido>{_escape(proveedor.razon_social)}</razonSocialSujetoRetenido>'
        f'<identificacionSujetoRetenido>{proveedor.identificacion}</identificacionSujetoRetenido>'
        f'<periodoFiscal>{retencion.periodo_fiscal}</periodoFiscal>'
        f'</infoCompRetencion>'
    )

    xml += '<docsSustento>'
    # Group detalles by document
    docs_procesados = {}
    for det in detalles:
        key = det.num_doc_sustento
        if key not in docs_procesados:
            docs_procesados[key] = {'det': det, 'impuestos': []}
        docs_procesados[key]['impuestos'].append(det)

    for key, doc_data in docs_procesados.items():
        det = doc_data['det']
        total_sin = float(det.base_0_doc or 0) + float(det.base_iva_doc or 0)
        xml += (
            f'<docSustento>'
            f'<codSustento>{_escape(det.codigo_sustento)}</codSustento>'
            f'<codDocSustento>{_escape(det.cod_doc_sustento)}</codDocSustento>'
            f'<numDocSustento>{_escape(det.num_doc_sustento)}</numDocSustento>'
            f'<fechaEmisionDocSustento>{_fmt_fecha(det.fecha_emision_doc_sustento)}</fechaEmisionDocSustento>'
            f'<numAutDocSustento>{_escape(det.num_aut_doc_sustento or "")}</numAutDocSustento>'
            f'<pagoLocExt>01</pagoLocExt>'
            f'<totalSinImpuestos>{total_sin:.2f}</totalSinImpuestos>'
            f'<importeTotal>{float(det.total_doc or 0):.2f}</importeTotal>'
            f'<impuestosDocSustento>'
        )
        if float(det.base_0_doc or 0) > 0:
            xml += (
                f'<impuestoDocSustento>'
                f'<codImpuestoDocSustento>2</codImpuestoDocSustento>'
                f'<codigoPorcentaje>0</codigoPorcentaje>'
                f'<baseImponible>{float(det.base_0_doc):.2f}</baseImponible>'
                f'<tarifa>0</tarifa>'
                f'<valorImpuesto>0.00</valorImpuesto>'
                f'</impuestoDocSustento>'
            )
        if float(det.base_iva_doc or 0) > 0:
            iva_val = round(float(det.base_iva_doc) * 0.12, 2)
            xml += (
                f'<impuestoDocSustento>'
                f'<codImpuestoDocSustento>2</codImpuestoDocSustento>'
                f'<codigoPorcentaje>2</codigoPorcentaje>'
                f'<baseImponible>{float(det.base_iva_doc):.2f}</baseImponible>'
                f'<tarifa>12</tarifa>'
                f'<valorImpuesto>{iva_val:.2f}</valorImpuesto>'
                f'</impuestoDocSustento>'
            )
        xml += '</impuestosDocSustento><retenciones>'
        for imp in doc_data['impuestos']:
            xml += (
                f'<retencion>'
                f'<codigo>{"1" if imp.tipo_retencion == "renta" else "2"}</codigo>'
                f'<codigoRetencion>{_escape(imp.codigo_retencion)}</codigoRetencion>'
                f'<baseImponible>{float(imp.base_imponible):.2f}</baseImponible>'
                f'<porcentajeRetener>{float(imp.porcentaje_retener):.2f}</porcentajeRetener>'
                f'<valorRetenido>{float(imp.valor_retenido):.2f}</valorRetenido>'
                f'</retencion>'
            )
        xml += '</retenciones></docSustento>'

    xml += '</docsSustento></comprobanteRetencion>'
    return xml


def generar_xml_nota_credito(empresa, cliente, nota, detalles) -> str:
    obligado = 'SI' if empresa.obligado_contabilidad else 'NO'
    contrib_especial = (
        f'<contribuyenteEspecial>{_escape(empresa.num_resolucion_contrib_especial)}</contribuyenteEspecial>'
        if empresa.contribuyente_especial else ''
    )
    total_sin = float(nota.subtotal_sin_impuesto or 0)

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<notaCredito id="comprobante" version="1.1.0">'
    )
    xml += _info_tributaria(empresa, '04', nota.clave_acceso,
                            empresa.establecimiento, empresa.punto_emision,
                            nota.numero)
    xml += (
        f'<infoNotaCredito>'
        f'<fechaEmision>{_fmt_fecha(nota.fecha_emision)}</fechaEmision>'
        f'<dirEstablecimiento>{_escape(empresa.direccion)}</dirEstablecimiento>'
        f'<tipoIdentificacionComprador>{cliente.tipo_identificacion}</tipoIdentificacionComprador>'
        f'<razonSocialComprador>{_escape(cliente.razon_social)}</razonSocialComprador>'
        f'<identificacionComprador>{cliente.identificacion}</identificacionComprador>'
        f'{contrib_especial}'
        f'<obligadoContabilidad>{obligado}</obligadoContabilidad>'
        f'<codDocModificado>{nota.tipo_doc_modificado}</codDocModificado>'
        f'<numDocModificado>{_escape(nota.num_doc_modificado)}</numDocModificado>'
        f'<fechaEmisionDocSustento>{_fmt_fecha(nota.fecha_doc_sustento)}</fechaEmisionDocSustento>'
        f'<totalSinImpuestos>{total_sin:.2f}</totalSinImpuestos>'
        f'<valorModificacion>{float(nota.total or 0):.2f}</valorModificacion>'
        f'<moneda>DOLAR</moneda>'
    )

    xml += '<totalConImpuestos>'
    if float(nota.subtotal_iva_0 or 0) > 0:
        xml += (
            f'<totalImpuesto><codigo>2</codigo><codigoPorcentaje>0</codigoPorcentaje>'
            f'<baseImponible>{float(nota.subtotal_iva_0):.2f}</baseImponible>'
            f'<valor>0.00</valor></totalImpuesto>'
        )
    if float(nota.subtotal_iva_12 or 0) > 0:
        xml += (
            f'<totalImpuesto><codigo>2</codigo><codigoPorcentaje>2</codigoPorcentaje>'
            f'<baseImponible>{float(nota.subtotal_iva_12):.2f}</baseImponible>'
            f'<valor>{float(nota.iva_12 or 0):.2f}</valor></totalImpuesto>'
        )
    xml += '</totalConImpuestos>'
    xml += (
        f'<motivo>{_escape(nota.motivo)}</motivo>'
        f'</infoNotaCredito>'
    )

    xml += '<detalles>'
    for det in detalles:
        xml += (
            f'<detalle>'
            f'<codigoInterno>{_escape(det.codigo_principal or "")}</codigoInterno>'
            f'<descripcion>{_escape(det.descripcion)}</descripcion>'
            f'<cantidad>{float(det.cantidad):.4f}</cantidad>'
            f'<precioUnitario>{float(det.precio_unitario):.4f}</precioUnitario>'
            f'<descuento>{float(det.descuento or 0):.2f}</descuento>'
            f'<precioTotalSinImpuesto>{float(det.precio_total_sin_impuesto):.2f}</precioTotalSinImpuesto>'
            f'<impuestos>'
            f'<impuesto>'
            f'<codigo>{det.impuesto_codigo or "2"}</codigo>'
            f'<codigoPorcentaje>{det.impuesto_codigo_porcentaje or "0"}</codigoPorcentaje>'
            f'<tarifa>{float(det.impuesto_tarifa or 0):.2f}</tarifa>'
            f'<baseImponible>{float(det.precio_total_sin_impuesto):.2f}</baseImponible>'
            f'<valor>{float(det.impuesto_valor or 0):.2f}</valor>'
            f'</impuesto>'
            f'</impuestos>'
            f'</detalle>'
        )
    xml += '</detalles>'

    if cliente.email:
        xml += (
            f'<infoAdicional>'
            f'<campoAdicional nombre="Email">{_escape(cliente.email)}</campoAdicional>'
            f'</infoAdicional>'
        )
    xml += '</notaCredito>'
    return xml


def generar_xml_nota_debito(empresa, cliente, nota, detalles) -> str:
    obligado = 'SI' if empresa.obligado_contabilidad else 'NO'
    contrib_especial = (
        f'<contribuyenteEspecial>{_escape(empresa.num_resolucion_contrib_especial)}</contribuyenteEspecial>'
        if empresa.contribuyente_especial else ''
    )
    total_sin = float(nota.subtotal_sin_impuesto or 0)

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<notaDebito id="comprobante" version="1.0.0">'
    )
    xml += _info_tributaria(empresa, '05', nota.clave_acceso,
                            empresa.establecimiento, empresa.punto_emision,
                            nota.numero)
    xml += (
        f'<infoNotaDebito>'
        f'<fechaEmision>{_fmt_fecha(nota.fecha_emision)}</fechaEmision>'
        f'<dirEstablecimiento>{_escape(empresa.direccion)}</dirEstablecimiento>'
        f'<tipoIdentificacionComprador>{cliente.tipo_identificacion}</tipoIdentificacionComprador>'
        f'<razonSocialComprador>{_escape(cliente.razon_social)}</razonSocialComprador>'
        f'<identificacionComprador>{cliente.identificacion}</identificacionComprador>'
        f'{contrib_especial}'
        f'<obligadoContabilidad>{obligado}</obligadoContabilidad>'
        f'<codDocModificado>{nota.tipo_doc_modificado}</codDocModificado>'
        f'<numDocModificado>{_escape(nota.num_doc_modificado)}</numDocModificado>'
        f'<fechaEmisionDocSustento>{_fmt_fecha(nota.fecha_doc_sustento)}</fechaEmisionDocSustento>'
        f'<totalSinImpuestos>{total_sin:.2f}</totalSinImpuestos>'
    )

    xml += '<impuestos>'
    if float(nota.subtotal_iva_0 or 0) > 0:
        xml += (
            f'<impuesto><codigo>2</codigo><codigoPorcentaje>0</codigoPorcentaje>'
            f'<tarifa>0</tarifa>'
            f'<baseImponible>{float(nota.subtotal_iva_0):.2f}</baseImponible>'
            f'<valor>0.00</valor></impuesto>'
        )
    if float(nota.subtotal_iva_12 or 0) > 0:
        xml += (
            f'<impuesto><codigo>2</codigo><codigoPorcentaje>2</codigoPorcentaje>'
            f'<tarifa>12</tarifa>'
            f'<baseImponible>{float(nota.subtotal_iva_12):.2f}</baseImponible>'
            f'<valor>{float(nota.iva_12 or 0):.2f}</valor></impuesto>'
        )
    xml += '</impuestos>'
    xml += (
        f'<valorTotal>{float(nota.total or 0):.2f}</valorTotal>'
        f'</infoNotaDebito>'
    )

    xml += '<motivos>'
    for det in detalles:
        xml += (
            f'<motivo>'
            f'<razon>{_escape(det.razon)}</razon>'
            f'<valor>{float(det.valor):.2f}</valor>'
            f'</motivo>'
        )
    xml += '</motivos>'

    if cliente.email:
        xml += (
            f'<infoAdicional>'
            f'<campoAdicional nombre="Email">{_escape(cliente.email)}</campoAdicional>'
            f'</infoAdicional>'
        )
    xml += '</notaDebito>'
    return xml


def generar_xml_guia_remision(empresa, guia, destinatarios) -> str:
    obligado = 'SI' if empresa.obligado_contabilidad else 'NO'
    contrib_especial = (
        f'<contribuyenteEspecial>{_escape(empresa.num_resolucion_contrib_especial)}</contribuyenteEspecial>'
        if empresa.contribuyente_especial else ''
    )
    tipo_id_transp = '04' if len(guia.ruc_transportista) == 13 else '05'

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<guiaRemision id="comprobante" version="1.0.0">'
    )
    xml += _info_tributaria(empresa, '06', guia.clave_acceso,
                            empresa.establecimiento, empresa.punto_emision,
                            guia.numero)
    xml += (
        f'<infoGuiaRemision>'
        f'<dirEstablecimiento>{_escape(empresa.direccion)}</dirEstablecimiento>'
        f'<dirPartida>{_escape(guia.dir_partida)}</dirPartida>'
        f'<razonSocialTransportista>{_escape(guia.razon_social_transportista)}</razonSocialTransportista>'
        f'<tipoIdentificacionTransportista>{tipo_id_transp}</tipoIdentificacionTransportista>'
        f'<rucTransportista>{guia.ruc_transportista}</rucTransportista>'
        f'<obligadoContabilidad>{obligado}</obligadoContabilidad>'
        f'{contrib_especial}'
        f'<fechaIniTransporte>{_fmt_fecha(guia.fecha_ini_transporte)}</fechaIniTransporte>'
        f'<fechaFinTransporte>{_fmt_fecha(guia.fecha_fin_transporte)}</fechaFinTransporte>'
        f'<placa>{_escape(guia.placa)}</placa>'
        f'</infoGuiaRemision>'
    )

    xml += '<destinatarios>'
    for dest in destinatarios:
        xml += (
            f'<destinatario>'
            f'<identificacionDestinatario>{_escape(dest.identificacion)}</identificacionDestinatario>'
            f'<razonSocialDestinatario>{_escape(dest.razon_social)}</razonSocialDestinatario>'
            f'<dirDestinatario>{_escape(dest.direccion_destino)}</dirDestinatario>'
            f'<motivoTraslado>{_escape(dest.motivo_traslado)}</motivoTraslado>'
        )
        if dest.num_doc_sustento:
            xml += (
                f'<codDocSustento>{dest.cod_doc_sustento or "01"}</codDocSustento>'
                f'<numDocSustento>{_escape(dest.num_doc_sustento)}</numDocSustento>'
                f'<numAutDocSustento>{_escape(dest.num_aut_doc_sustento or "")}</numAutDocSustento>'
                f'<fechaEmisionDocSustento>{_fmt_fecha(dest.fecha_emision_doc_sustento)}</fechaEmisionDocSustento>'
            )
        xml += '<detalles>'
        for det in dest.detalles:
            xml += (
                f'<detalle>'
                f'<codigoInterno>{_escape(det.codigo_interno or "")}</codigoInterno>'
                f'<descripcion>{_escape(det.descripcion)}</descripcion>'
                f'<cantidad>{float(det.cantidad):.2f}</cantidad>'
                f'</detalle>'
            )
        xml += '</detalles></destinatario>'
    xml += '</destinatarios>'
    xml += '</guiaRemision>'
    return xml


def generar_xml_liquidacion(empresa, proveedor, liquidacion, detalles) -> str:
    obligado = 'SI' if empresa.obligado_contabilidad else 'NO'
    contrib_especial = (
        f'<contribuyenteEspecial>{_escape(empresa.num_resolucion_contrib_especial)}</contribuyenteEspecial>'
        if empresa.contribuyente_especial else ''
    )
    total_sin = float(liquidacion.subtotal_sin_impuesto or 0)

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<liquidacionCompra id="comprobante" version="1.1.0">'
    )
    xml += _info_tributaria(empresa, '03', liquidacion.clave_acceso,
                            empresa.establecimiento, empresa.punto_emision,
                            liquidacion.numero)
    xml += (
        f'<infoLiquidacionCompra>'
        f'<fechaEmision>{_fmt_fecha(liquidacion.fecha_emision)}</fechaEmision>'
        f'<dirEstablecimiento>{_escape(empresa.direccion)}</dirEstablecimiento>'
        f'{contrib_especial}'
        f'<obligadoContabilidad>{obligado}</obligadoContabilidad>'
        f'<tipoIdentificacionProveedor>{proveedor.tipo_identificacion}</tipoIdentificacionProveedor>'
        f'<razonSocialProveedor>{_escape(proveedor.razon_social)}</razonSocialProveedor>'
        f'<identificacionProveedor>{proveedor.identificacion}</identificacionProveedor>'
        f'<direccionProveedor>{_escape(proveedor.direccion or "")}</direccionProveedor>'
        f'<totalSinImpuestos>{total_sin:.2f}</totalSinImpuestos>'
        f'<totalDescuento>{float(liquidacion.descuento_total or 0):.2f}</totalDescuento>'
    )

    xml += '<totalConImpuestos>'
    if float(liquidacion.subtotal_iva_0 or 0) > 0:
        xml += (
            f'<totalImpuesto><codigo>2</codigo><codigoPorcentaje>0</codigoPorcentaje>'
            f'<baseImponible>{float(liquidacion.subtotal_iva_0):.2f}</baseImponible>'
            f'<valor>0.00</valor></totalImpuesto>'
        )
    if float(liquidacion.subtotal_iva_12 or 0) > 0:
        xml += (
            f'<totalImpuesto><codigo>2</codigo><codigoPorcentaje>2</codigoPorcentaje>'
            f'<baseImponible>{float(liquidacion.subtotal_iva_12):.2f}</baseImponible>'
            f'<valor>{float(liquidacion.iva_12 or 0):.2f}</valor></totalImpuesto>'
        )
    xml += '</totalConImpuestos>'

    xml += (
        f'<importeTotal>{float(liquidacion.total or 0):.2f}</importeTotal>'
        f'<moneda>DOLAR</moneda>'
        f'<pagos>'
        f'<pago>'
        f'<formaPago>{liquidacion.forma_pago or "01"}</formaPago>'
        f'<total>{float(liquidacion.total or 0):.2f}</total>'
        f'</pago>'
        f'</pagos>'
        f'</infoLiquidacionCompra>'
    )

    xml += '<detalles>'
    for det in detalles:
        xml += (
            f'<detalle>'
            f'<codigoPrincipal>{_escape(det.codigo_principal or "")}</codigoPrincipal>'
            f'<descripcion>{_escape(det.descripcion)}</descripcion>'
            f'<cantidad>{float(det.cantidad):.4f}</cantidad>'
            f'<precioUnitario>{float(det.precio_unitario):.4f}</precioUnitario>'
            f'<descuento>{float(det.descuento or 0):.2f}</descuento>'
            f'<precioTotalSinImpuesto>{float(det.precio_total_sin_impuesto):.2f}</precioTotalSinImpuesto>'
            f'<impuestos>'
            f'<impuesto>'
            f'<codigo>{det.impuesto_codigo or "2"}</codigo>'
            f'<codigoPorcentaje>{det.impuesto_codigo_porcentaje or "0"}</codigoPorcentaje>'
            f'<tarifa>{float(det.impuesto_tarifa or 0):.2f}</tarifa>'
            f'<baseImponible>{float(det.precio_total_sin_impuesto):.2f}</baseImponible>'
            f'<valor>{float(det.impuesto_valor or 0):.2f}</valor>'
            f'</impuesto>'
            f'</impuestos>'
            f'</detalle>'
        )
    xml += '</detalles>'
    xml += '</liquidacionCompra>'
    return xml
