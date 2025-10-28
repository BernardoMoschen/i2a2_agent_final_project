"""XML parser tool for fiscal documents."""

from decimal import Decimal
from xml.etree.ElementTree import Element

from defusedxml import ElementTree as ET

from src.models import DocumentType, InvoiceItem, InvoiceModel, TaxDetails


class XMLParserTool:
    """Safe XML parser for Brazilian fiscal documents (NFe, NFCe, CTe, MDFe)."""

    # Namespace prefixes commonly found in fiscal XMLs
    NAMESPACES = {
        "nfe": "http://www.portalfiscal.inf.br/nfe",
        "cte": "http://www.portalfiscal.inf.br/cte",
        "mdfe": "http://www.portalfiscal.inf.br/mdfe",
    }

    def parse(self, xml_content: str) -> InvoiceModel:
        """
        Parse fiscal XML into normalized InvoiceModel.

        Args:
            xml_content: Raw XML string

        Returns:
            InvoiceModel with normalized data

        Raises:
            ValueError: If XML is malformed or unsupported document type
        """
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            raise ValueError(f"Malformed XML: {e}") from e

        # Detect document type from root tag
        doc_type = self._detect_document_type(root)

        # Route to appropriate parser
        if doc_type == DocumentType.NFE or doc_type == DocumentType.NFCE:
            return self._parse_nfe(root, xml_content, doc_type)
        elif doc_type == DocumentType.CTE:
            return self._parse_cte(root, xml_content)
        elif doc_type == DocumentType.MDFE:
            return self._parse_mdfe(root, xml_content)
        else:
            raise ValueError(f"Unsupported document type: {doc_type}")

    def _detect_document_type(self, root: Element) -> DocumentType:
        """Detect document type from XML root."""
        tag = root.tag.split("}")[-1]  # Remove namespace
        if tag in ("NFe", "nfeProc"):
            # Check if it's NFCe by examining the model field (mod)
            mod_elem = root.find(".//mod", self.NAMESPACES)
            if mod_elem is None:
                mod_elem = root.find(".//nfe:mod", self.NAMESPACES)
            # Try without namespace if not found
            if mod_elem is None:
                for elem in root.iter():
                    if elem.tag.endswith("mod"):
                        mod_elem = elem
                        break
            if mod_elem is not None and mod_elem.text == "65":
                return DocumentType.NFCE
            return DocumentType.NFE
        elif tag in ("CTe", "cteProc"):
            return DocumentType.CTE
        elif tag in ("MDFe", "mdfeProc"):
            return DocumentType.MDFE
        else:
            raise ValueError(f"Unknown document type from tag: {tag}")

    def _parse_nfe(self, root: Element, xml_content: str, doc_type: DocumentType) -> InvoiceModel:
        """Parse NFe/NFCe XML."""
        # Find the infNFe element (contains all invoice data)
        inf_nfe = root.find(".//infNFe", self.NAMESPACES) or root.find(
            ".//nfe:infNFe", self.NAMESPACES
        )
        if inf_nfe is None:
            raise ValueError("Missing infNFe element in NFe XML")

        # Extract document key from attribute
        document_key = inf_nfe.get("Id", "").replace("NFe", "")

        # IDE section (identification)
        ide = inf_nfe.find(".//ide", self.NAMESPACES) or inf_nfe.find(".//nfe:ide", self.NAMESPACES)
        if ide is None:
            raise ValueError("Missing ide element in NFe XML")

        document_number = self._get_text(ide, "nNF")
        series = self._get_text(ide, "serie")
        issue_date_str = self._get_text(ide, "dhEmi")

        # Parse issue date (format: 2024-01-15T10:30:00-03:00)
        from datetime import datetime

        issue_date = datetime.fromisoformat(issue_date_str.replace("Z", "+00:00"))

        # Emit section (issuer)
        emit = inf_nfe.find(".//emit", self.NAMESPACES) or inf_nfe.find(
            ".//nfe:emit", self.NAMESPACES
        )
        if emit is None:
            raise ValueError("Missing emit element in NFe XML")

        issuer_cnpj = self._get_text(emit, "CNPJ")
        issuer_name = self._get_text(emit, "xNome")
        
        # Extract tax regime (CRT) - NEW
        tax_regime = self._get_text(emit, "CRT")
        
        # Extract issuer IE (Inscrição Estadual) - NEW
        issuer_ie = self._get_text(emit, "IE")
        
        # Extract issuer UF - NEW
        issuer_uf = self._get_text(emit, "UF")
        issuer_municipio = None
        issuer_cep = None
        if not issuer_uf:
            # Try enderEmit/UF
            ender_emit = emit.find(".//enderEmit", self.NAMESPACES) or emit.find(".//nfe:enderEmit", self.NAMESPACES)
            if ender_emit is not None:
                issuer_uf = self._get_text(ender_emit, "UF")
                issuer_municipio = self._get_text(ender_emit, "xMun")
                issuer_cep = self._get_text(ender_emit, "CEP")
        else:
            # Also try to get municipio and CEP
            ender_emit = emit.find(".//enderEmit", self.NAMESPACES) or emit.find(".//nfe:enderEmit", self.NAMESPACES)
            if ender_emit is not None:
                issuer_municipio = self._get_text(ender_emit, "xMun")
                issuer_cep = self._get_text(ender_emit, "CEP")

        # Dest section (recipient) - optional for NFCe
        dest = inf_nfe.find(".//dest", self.NAMESPACES) or inf_nfe.find(
            ".//nfe:dest", self.NAMESPACES
        )
        recipient_cnpj_cpf = None
        recipient_name = None
        recipient_uf = None
        recipient_municipio = None
        recipient_cep = None
        recipient_ie = None
        if dest is not None:
            recipient_cnpj_cpf = self._get_text(dest, "CNPJ") or self._get_text(dest, "CPF")
            recipient_name = self._get_text(dest, "xNome")
            recipient_ie = self._get_text(dest, "IE")
            
            # Extract recipient UF - NEW
            recipient_uf = self._get_text(dest, "UF")
            if not recipient_uf:
                # Try enderDest/UF
                ender_dest = dest.find(".//enderDest", self.NAMESPACES) or dest.find(".//nfe:enderDest", self.NAMESPACES)
                if ender_dest is not None:
                    recipient_uf = self._get_text(ender_dest, "UF")
                    recipient_municipio = self._get_text(ender_dest, "xMun")
                    recipient_cep = self._get_text(ender_dest, "CEP")
            else:
                # Also try to get municipio and CEP
                ender_dest = dest.find(".//enderDest", self.NAMESPACES) or dest.find(".//nfe:enderDest", self.NAMESPACES)
                if ender_dest is not None:
                    recipient_municipio = self._get_text(ender_dest, "xMun")
                    recipient_cep = self._get_text(ender_dest, "CEP")

        # Total section
        total = inf_nfe.find(".//total/ICMSTot", self.NAMESPACES) or inf_nfe.find(
            ".//nfe:total/nfe:ICMSTot", self.NAMESPACES
        )
        if total is None:
            raise ValueError("Missing total/ICMSTot element in NFe XML")

        total_products = Decimal(self._get_text(total, "vProd") or "0")
        total_invoice = Decimal(self._get_text(total, "vNF") or "0")
        
        # Extract discount and other expenses - NEW
        discount = Decimal(self._get_text(total, "vDesc") or "0")
        other_expenses = Decimal(self._get_text(total, "vOutro") or "0")

        # Calculate total taxes
        icms_total = Decimal(self._get_text(total, "vICMS") or "0")
        ipi_total = Decimal(self._get_text(total, "vIPI") or "0")
        pis_total = Decimal(self._get_text(total, "vPIS") or "0")
        cofins_total = Decimal(self._get_text(total, "vCOFINS") or "0")
        total_taxes = icms_total + ipi_total + pis_total + cofins_total

        # Parse items
        items = self._parse_nfe_items(inf_nfe)

        # Build tax details
        taxes = TaxDetails(
            icms=icms_total,
            ipi=ipi_total,
            pis=pis_total,
            cofins=cofins_total,
        )

        return InvoiceModel(
            document_type=doc_type,
            document_key=document_key,
            document_number=document_number,
            series=series,
            issue_date=issue_date,
            issuer_cnpj=issuer_cnpj,
            issuer_name=issuer_name,
            recipient_cnpj_cpf=recipient_cnpj_cpf,
            recipient_name=recipient_name,
            issuer_uf=issuer_uf,
            recipient_uf=recipient_uf,
            issuer_municipio=issuer_municipio,
            recipient_municipio=recipient_municipio,
            issuer_cep=issuer_cep,
            recipient_cep=recipient_cep,
            issuer_ie=issuer_ie,
            recipient_ie=recipient_ie,
            tax_regime=tax_regime,
            total_products=total_products,
            total_taxes=total_taxes,
            total_invoice=total_invoice,
            discount=discount,
            other_expenses=other_expenses,
            items=items,
            taxes=taxes,
            raw_xml=xml_content,
        )

    def _parse_nfe_items(self, inf_nfe: Element) -> list[InvoiceItem]:
        """Parse items from NFe XML."""
        items = []
        det_elements = inf_nfe.findall(".//det", self.NAMESPACES) or inf_nfe.findall(
            ".//nfe:det", self.NAMESPACES
        )

        for idx, det in enumerate(det_elements, start=1):
            prod = det.find(".//prod", self.NAMESPACES) or det.find(".//nfe:prod", self.NAMESPACES)
            if prod is None:
                continue

            product_code = self._get_text(prod, "cProd")
            description = self._get_text(prod, "xProd")
            ncm = self._get_text(prod, "NCM")
            cfop = self._get_text(prod, "CFOP")
            unit = self._get_text(prod, "uCom")
            quantity = Decimal(self._get_text(prod, "qCom") or "0")
            unit_price = Decimal(self._get_text(prod, "vUnCom") or "0")
            total_price = Decimal(self._get_text(prod, "vProd") or "0")

            # Parse taxes for this item
            imposto = det.find(".//imposto", self.NAMESPACES) or det.find(
                ".//nfe:imposto", self.NAMESPACES
            )
            item_taxes = TaxDetails()
            cst = None
            icms_origin = None
            icms_rate = None
            icms_base = None
            
            if imposto is not None:
                icms = imposto.find(".//ICMS", self.NAMESPACES) or imposto.find(
                    ".//nfe:ICMS", self.NAMESPACES
                )
                if icms is not None:
                    # ICMS can have multiple variants (ICMS00, ICMS10, ICMS40, etc.)
                    for child in icms:
                        # Extract CST or CSOSN - NEW
                        cst_val = self._get_text(child, "CST") or self._get_text(child, "CSOSN")
                        if cst_val:
                            cst = cst_val
                        
                        # Extract origin - NEW
                        orig_val = self._get_text(child, "orig")
                        if orig_val:
                            icms_origin = orig_val
                        
                        # Extract ICMS rate - NEW
                        rate_val = self._get_text(child, "pICMS")
                        if rate_val:
                            icms_rate = Decimal(rate_val)
                        
                        # Extract ICMS base - NEW
                        base_val = self._get_text(child, "vBC")
                        if base_val:
                            icms_base = Decimal(base_val)
                        
                        # Extract ICMS value
                        icms_val = self._get_text(child, "vICMS")
                        if icms_val:
                            item_taxes.icms = Decimal(icms_val)
                            break

                ipi = imposto.find(".//IPI/IPITrib", self.NAMESPACES) or imposto.find(
                    ".//nfe:IPI/nfe:IPITrib", self.NAMESPACES
                )
                if ipi is not None:
                    ipi_val = self._get_text(ipi, "vIPI")
                    if ipi_val:
                        item_taxes.ipi = Decimal(ipi_val)

                pis = imposto.find(".//PIS", self.NAMESPACES) or imposto.find(
                    ".//nfe:PIS", self.NAMESPACES
                )
                if pis is not None:
                    for child in pis:
                        pis_val = self._get_text(child, "vPIS")
                        if pis_val:
                            item_taxes.pis = Decimal(pis_val)
                            break

                cofins = imposto.find(".//COFINS", self.NAMESPACES) or imposto.find(
                    ".//nfe:COFINS", self.NAMESPACES
                )
                if cofins is not None:
                    for child in cofins:
                        cofins_val = self._get_text(child, "vCOFINS")
                        if cofins_val:
                            item_taxes.cofins = Decimal(cofins_val)
                            break

            items.append(
                InvoiceItem(
                    item_number=idx,
                    product_code=product_code,
                    description=description,
                    ncm=ncm,
                    cfop=cfop,
                    unit=unit,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price,
                    taxes=item_taxes,
                    cst=cst,
                    icms_origin=icms_origin,
                    icms_rate=icms_rate,
                    icms_base=icms_base,
                )
            )

        return items

    def _parse_cte(self, root: Element, xml_content: str) -> InvoiceModel:
        """
        Parse CTe (Conhecimento de Transporte Eletrônico) XML.
        
        CTe is a transport document - adapts to InvoiceModel structure:
        - "items" will be empty (transport has no product items)
        - total_products = transport service value
        - issuer = transport company
        - recipient = freight payer (can be sender, recipient, or third party)
        """
        # Find infCte element
        inf_cte = root.find(".//infCte", self.NAMESPACES) or root.find(".//cte:infCte", self.NAMESPACES)
        if inf_cte is None:
            raise ValueError("Missing infCte element in CTe XML")
        
        # Extract document key
        document_key = inf_cte.get("Id", "").replace("CTe", "")
        
        # IDE section (identification)
        ide = inf_cte.find(".//ide", self.NAMESPACES) or inf_cte.find(".//cte:ide", self.NAMESPACES)
        if ide is None:
            raise ValueError("Missing ide element in CTe XML")
        
        document_number = self._get_text(ide, "nCT")
        series = self._get_text(ide, "serie")
        issue_date_str = self._get_text(ide, "dhEmi")
        
        # Parse issue date
        from datetime import datetime
        issue_date = datetime.fromisoformat(issue_date_str.replace("Z", "+00:00"))
        
        # Emit section (transport company - issuer)
        emit = inf_cte.find(".//emit", self.NAMESPACES) or inf_cte.find(".//cte:emit", self.NAMESPACES)
        if emit is None:
            raise ValueError("Missing emit element in CTe XML")
        
        issuer_cnpj = self._get_text(emit, "CNPJ")
        issuer_name = self._get_text(emit, "xNome")
        issuer_ie = self._get_text(emit, "IE")
        
        # Extract issuer address
        ender_emit = emit.find(".//enderEmit", self.NAMESPACES) or emit.find(".//cte:enderEmit", self.NAMESPACES)
        issuer_uf = None
        issuer_municipio = None
        issuer_cep = None
        if ender_emit is not None:
            issuer_uf = self._get_text(ender_emit, "UF")
            issuer_municipio = self._get_text(ender_emit, "xMun")
            issuer_cep = self._get_text(ender_emit, "CEP")
        
        # Recipient (freight payer - can be rem/dest/exped/receb)
        # Priority: try to get dest (recipient), then rem (sender)
        recipient_cnpj_cpf = None
        recipient_name = None
        recipient_uf = None
        recipient_municipio = None
        recipient_cep = None
        recipient_ie = None
        
        # Try dest first
        dest = inf_cte.find(".//dest", self.NAMESPACES) or inf_cte.find(".//cte:dest", self.NAMESPACES)
        if dest is None:
            # Try rem (sender) as fallback
            dest = inf_cte.find(".//rem", self.NAMESPACES) or inf_cte.find(".//cte:rem", self.NAMESPACES)
        
        if dest is not None:
            recipient_cnpj_cpf = self._get_text(dest, "CNPJ") or self._get_text(dest, "CPF")
            recipient_name = self._get_text(dest, "xNome")
            recipient_ie = self._get_text(dest, "IE")
            
            # Extract recipient address
            ender_dest = dest.find(".//enderDest", self.NAMESPACES) or dest.find(".//cte:enderDest", self.NAMESPACES)
            if ender_dest is None:
                ender_dest = dest.find(".//enderReme", self.NAMESPACES) or dest.find(".//cte:enderReme", self.NAMESPACES)
            
            if ender_dest is not None:
                recipient_uf = self._get_text(ender_dest, "UF")
                recipient_municipio = self._get_text(ender_dest, "xMun")
                recipient_cep = self._get_text(ender_dest, "CEP")
        
        # vPrest section (transport service value)
        v_prest = inf_cte.find(".//vPrest", self.NAMESPACES) or inf_cte.find(".//cte:vPrest", self.NAMESPACES)
        if v_prest is None:
            raise ValueError("Missing vPrest element in CTe XML")
        
        total_invoice = Decimal(self._get_text(v_prest, "vTPrest") or "0")
        total_products = total_invoice  # Transport service value
        
        # Extract tax values
        icms_total = Decimal(self._get_text(v_prest, "vICMS") or "0")
        
        # Imp section (taxes) - optional
        imp = inf_cte.find(".//imp", self.NAMESPACES) or inf_cte.find(".//cte:imp", self.NAMESPACES)
        if imp is not None:
            icms_elem = imp.find(".//ICMS", self.NAMESPACES) or imp.find(".//cte:ICMS", self.NAMESPACES)
            if icms_elem is not None:
                # ICMS can have variants (ICMS00, ICMS20, ICMS45, ICMS90, ICMSSN)
                for child in icms_elem:
                    icms_val = self._get_text(child, "vICMS")
                    if icms_val:
                        icms_total = Decimal(icms_val)
                        break
        
        total_taxes = icms_total  # CTe typically only has ICMS
        
        # Build tax details
        taxes = TaxDetails(
            icms=icms_total,
            ipi=Decimal("0"),
            pis=Decimal("0"),
            cofins=Decimal("0"),
        )
        
        return InvoiceModel(
            document_type=DocumentType.CTE,
            document_key=document_key,
            document_number=document_number,
            series=series,
            issue_date=issue_date,
            issuer_cnpj=issuer_cnpj,
            issuer_name=issuer_name,
            recipient_cnpj_cpf=recipient_cnpj_cpf,
            recipient_name=recipient_name,
            issuer_uf=issuer_uf,
            recipient_uf=recipient_uf,
            issuer_municipio=issuer_municipio,
            recipient_municipio=recipient_municipio,
            issuer_cep=issuer_cep,
            recipient_cep=recipient_cep,
            issuer_ie=issuer_ie,
            recipient_ie=recipient_ie,
            tax_regime=None,  # CTe doesn't have CRT
            total_products=total_products,
            total_taxes=total_taxes,
            total_invoice=total_invoice,
            discount=Decimal("0"),
            other_expenses=Decimal("0"),
            items=[],  # CTe has no product items
            taxes=taxes,
            raw_xml=xml_content,
        )

    def _parse_mdfe(self, root: Element, xml_content: str) -> InvoiceModel:
        """
        Parse MDFe (Manifesto Eletrônico de Documentos Fiscais) XML.
        
        MDFe is a manifest document - adapts to InvoiceModel structure:
        - "items" will be empty (manifest doesn't have product items)
        - total_products/invoice = 0 (manifest doesn't have monetary value)
        - issuer = transport company
        - recipient = first destination (if available)
        """
        # Find infMDFe element
        inf_mdfe = root.find(".//infMDFe", self.NAMESPACES) or root.find(".//mdfe:infMDFe", self.NAMESPACES)
        if inf_mdfe is None:
            raise ValueError("Missing infMDFe element in MDFe XML")
        
        # Extract document key
        document_key = inf_mdfe.get("Id", "").replace("MDFe", "")
        
        # IDE section (identification)
        ide = inf_mdfe.find(".//ide", self.NAMESPACES) or inf_mdfe.find(".//mdfe:ide", self.NAMESPACES)
        if ide is None:
            raise ValueError("Missing ide element in MDFe XML")
        
        document_number = self._get_text(ide, "nMDF")
        series = self._get_text(ide, "serie")
        issue_date_str = self._get_text(ide, "dhEmi")
        
        # Parse issue date
        from datetime import datetime
        issue_date = datetime.fromisoformat(issue_date_str.replace("Z", "+00:00"))
        
        # Emit section (transport company - issuer)
        emit = inf_mdfe.find(".//emit", self.NAMESPACES) or inf_mdfe.find(".//mdfe:emit", self.NAMESPACES)
        if emit is None:
            raise ValueError("Missing emit element in MDFe XML")
        
        issuer_cnpj = self._get_text(emit, "CNPJ")
        issuer_name = self._get_text(emit, "xNome")
        issuer_ie = self._get_text(emit, "IE")
        
        # Extract issuer address
        ender_emit = emit.find(".//enderEmit", self.NAMESPACES) or emit.find(".//mdfe:enderEmit", self.NAMESPACES)
        issuer_uf = None
        issuer_municipio = None
        issuer_cep = None
        if ender_emit is not None:
            issuer_uf = self._get_text(ender_emit, "UF")
            issuer_municipio = self._get_text(ender_emit, "xMun")
            issuer_cep = self._get_text(ender_emit, "CEP")
        
        # Recipient (first destination UF)
        # MDFe doesn't have a traditional recipient, get from first infPercurso/infMunCarrega
        recipient_uf = None
        recipient_municipio = None
        
        # Try to get from infPercurso (route)
        inf_percurso = inf_mdfe.find(".//infPercurso", self.NAMESPACES) or inf_mdfe.find(".//mdfe:infPercurso", self.NAMESPACES)
        if inf_percurso is not None:
            recipient_uf = self._get_text(inf_percurso, "UFPer")
        
        # If not found, try infMunCarrega (loading municipality)
        if not recipient_uf:
            inf_mun_carrega = inf_mdfe.find(".//infMunCarrega", self.NAMESPACES) or inf_mdfe.find(".//mdfe:infMunCarrega", self.NAMESPACES)
            if inf_mun_carrega is not None:
                recipient_municipio = self._get_text(inf_mun_carrega, "xMunCarrega")
        
        # MDFe doesn't have monetary values (it's just a manifest)
        total_products = Decimal("0")
        total_taxes = Decimal("0")
        total_invoice = Decimal("0")
        
        # Build empty tax details
        taxes = TaxDetails(
            icms=Decimal("0"),
            ipi=Decimal("0"),
            pis=Decimal("0"),
            cofins=Decimal("0"),
        )
        
        return InvoiceModel(
            document_type=DocumentType.MDFE,
            document_key=document_key,
            document_number=document_number,
            series=series,
            issue_date=issue_date,
            issuer_cnpj=issuer_cnpj,
            issuer_name=issuer_name,
            recipient_cnpj_cpf=None,  # MDFe doesn't have traditional recipient
            recipient_name=None,
            issuer_uf=issuer_uf,
            recipient_uf=recipient_uf,
            issuer_municipio=issuer_municipio,
            recipient_municipio=recipient_municipio,
            issuer_cep=issuer_cep,
            recipient_cep=None,
            issuer_ie=issuer_ie,
            recipient_ie=None,
            tax_regime=None,  # MDFe doesn't have CRT
            total_products=total_products,
            total_taxes=total_taxes,
            total_invoice=total_invoice,
            discount=Decimal("0"),
            other_expenses=Decimal("0"),
            items=[],  # MDFe has no product items
            taxes=taxes,
            raw_xml=xml_content,
        )

    def _get_text(self, element: Element, tag: str) -> str:
        """Safely extract text from XML element."""
        child = element.find(f".//{tag}", self.NAMESPACES)
        if child is None:
            child = element.find(f".//nfe:{tag}", self.NAMESPACES)
        if child is None:
            child = element.find(f".//cte:{tag}", self.NAMESPACES)
        if child is None:
            child = element.find(f".//mdfe:{tag}", self.NAMESPACES)
        return child.text if child is not None and child.text else ""
