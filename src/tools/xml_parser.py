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

        # Dest section (recipient) - optional for NFCe
        dest = inf_nfe.find(".//dest", self.NAMESPACES) or inf_nfe.find(
            ".//nfe:dest", self.NAMESPACES
        )
        recipient_cnpj_cpf = None
        recipient_name = None
        if dest is not None:
            recipient_cnpj_cpf = self._get_text(dest, "CNPJ") or self._get_text(dest, "CPF")
            recipient_name = self._get_text(dest, "xNome")

        # Total section
        total = inf_nfe.find(".//total/ICMSTot", self.NAMESPACES) or inf_nfe.find(
            ".//nfe:total/nfe:ICMSTot", self.NAMESPACES
        )
        if total is None:
            raise ValueError("Missing total/ICMSTot element in NFe XML")

        total_products = Decimal(self._get_text(total, "vProd") or "0")
        total_invoice = Decimal(self._get_text(total, "vNF") or "0")

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
            total_products=total_products,
            total_taxes=total_taxes,
            total_invoice=total_invoice,
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
            if imposto is not None:
                icms = imposto.find(".//ICMS", self.NAMESPACES) or imposto.find(
                    ".//nfe:ICMS", self.NAMESPACES
                )
                if icms is not None:
                    # ICMS can have multiple variants (ICMS00, ICMS10, etc.)
                    for child in icms:
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
                )
            )

        return items

    def _parse_cte(self, root: Element, xml_content: str) -> InvoiceModel:
        """Parse CTe XML (stub implementation)."""
        # TODO: Implement full CTe parser
        raise NotImplementedError("CTe parsing not yet implemented")

    def _parse_mdfe(self, root: Element, xml_content: str) -> InvoiceModel:
        """Parse MDFe XML (stub implementation)."""
        # TODO: Implement full MDFe parser
        raise NotImplementedError("MDFe parsing not yet implemented")

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
