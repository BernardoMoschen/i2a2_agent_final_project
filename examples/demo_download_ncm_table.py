#!/usr/bin/env python3
"""
Script to download and process official NCM table from Receita Federal.

This script:
1. Downloads TIPI table from Receita Federal (or uses manual CSV)
2. Parses the data and extracts NCM codes
3. Generates expanded ncm_codes.csv with all official codes
4. Validates format and removes duplicates

Sources:
- TIPI (Tabela de Incidência do IPI): Receita Federal
- NCM Structure: 8 digits (CHAPTER.POSITION.SUBPOSITION.ITEM.SUBITEM)

Usage:
    python scripts/download_ncm_table.py [--source tipi|manual]
    
    Options:
    --source tipi      : Download from Receita Federal (requires parsing PDF/Excel)
    --source manual    : Use manually downloaded CSV file
    --input <file>     : Path to manually downloaded NCM CSV/Excel
    --output <file>    : Output path for ncm_codes.csv (default: data/ncm_codes.csv)
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import List, Dict, Set
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NCMTableDownloader:
    """Download and process official NCM table."""
    
    def __init__(self, output_path: Path):
        """
        Initialize NCM table downloader.
        
        Args:
            output_path: Path where to save processed ncm_codes.csv
        """
        self.output_path = output_path
        self.ncm_data: List[Dict[str, str]] = []
    
    def download_from_tipi_pdf(self) -> bool:
        """
        Download TIPI table from Receita Federal (PDF format).
        
        Note: This requires manual implementation as TIPI format changes.
        For production use, download manually and use process_manual_csv().
        
        Returns:
            bool: True if successful
        """
        logger.warning("Automated PDF download not implemented.")
        logger.info("Please download TIPI manually from:")
        logger.info("  https://www.gov.br/receitafederal/pt-br")
        logger.info("  Search for: 'TIPI' or 'Tabela de Incidência do IPI'")
        logger.info("")
        logger.info("After downloading, convert to CSV with columns:")
        logger.info("  ncm,description,ipi_rate")
        logger.info("")
        logger.info("Then run: python scripts/download_ncm_table.py --source manual --input <your_file.csv>")
        return False
    
    def download_from_siscomex(self) -> bool:
        """
        Download NCM table from Siscomex API.
        
        Note: Requires API credentials. For production, use manual CSV.
        
        Returns:
            bool: True if successful
        """
        logger.warning("Siscomex API integration not implemented.")
        logger.info("Siscomex requires authentication and API access.")
        logger.info("Please use manual CSV download instead.")
        return False
    
    def process_manual_csv(self, input_path: Path) -> bool:
        """
        Process manually downloaded NCM CSV file.
        
        Expected CSV format:
            ncm,description,ipi_rate
            01011000,Cavalos reprodutores de raça pura,0
            01012100,Cavalos vivos,2
            ...
        
        Or simplified format:
            ncm,description
            01011000,Cavalos reprodutores de raça pura
            01012100,Cavalos vivos
            ...
        
        Args:
            input_path: Path to manually downloaded CSV
        
        Returns:
            bool: True if successful
        """
        logger.info(f"Processing manual CSV: {input_path}")
        
        if not input_path.exists():
            logger.error(f"File not found: {input_path}")
            return False
        
        try:
            with open(input_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                # Validate headers
                if 'ncm' not in reader.fieldnames:
                    logger.error("CSV must have 'ncm' column")
                    return False
                
                has_description = 'description' in reader.fieldnames
                has_ipi = 'ipi_rate' in reader.fieldnames
                
                for row in reader:
                    ncm = row['ncm'].strip()
                    
                    # Validate NCM format (8 digits)
                    ncm_clean = ''.join(c for c in ncm if c.isdigit())
                    
                    if len(ncm_clean) != 8:
                        logger.warning(f"Invalid NCM format (not 8 digits): {ncm}")
                        continue
                    
                    ncm_entry = {
                        'ncm': ncm_clean,
                        'description': row.get('description', '').strip() if has_description else '',
                        'ipi_rate': row.get('ipi_rate', '').strip() if has_ipi else '',
                    }
                    
                    self.ncm_data.append(ncm_entry)
            
            logger.info(f"Loaded {len(self.ncm_data)} NCM codes from CSV")
            return True
            
        except Exception as e:
            logger.error(f"Error processing CSV: {e}")
            return False
    
    def process_manual_excel(self, input_path: Path) -> bool:
        """
        Process manually downloaded NCM Excel file.
        
        Requires: openpyxl or pandas
        
        Args:
            input_path: Path to Excel file
        
        Returns:
            bool: True if successful
        """
        logger.info(f"Processing Excel file: {input_path}")
        
        try:
            import pandas as pd
        except ImportError:
            logger.error("pandas not installed. Install with: pip install pandas openpyxl")
            return False
        
        try:
            # Read Excel file
            df = pd.read_excel(input_path)
            
            # Normalize column names
            df.columns = df.columns.str.lower().str.strip()
            
            if 'ncm' not in df.columns:
                logger.error("Excel must have 'ncm' column")
                logger.info(f"Found columns: {list(df.columns)}")
                return False
            
            # Process each row
            for _, row in df.iterrows():
                ncm = str(row['ncm']).strip()
                
                # Clean NCM (remove dots, spaces)
                ncm_clean = ''.join(c for c in ncm if c.isdigit())
                
                if len(ncm_clean) != 8:
                    continue
                
                ncm_entry = {
                    'ncm': ncm_clean,
                    'description': str(row.get('description', row.get('descricao', ''))).strip(),
                    'ipi_rate': str(row.get('ipi_rate', row.get('aliquota_ipi', ''))).strip(),
                }
                
                self.ncm_data.append(ncm_entry)
            
            logger.info(f"Loaded {len(self.ncm_data)} NCM codes from Excel")
            return True
            
        except Exception as e:
            logger.error(f"Error processing Excel: {e}")
            return False
    
    def remove_duplicates(self) -> int:
        """
        Remove duplicate NCM codes (keep first occurrence).
        
        Returns:
            int: Number of duplicates removed
        """
        seen: Set[str] = set()
        unique_data: List[Dict[str, str]] = []
        duplicates = 0
        
        for entry in self.ncm_data:
            ncm = entry['ncm']
            if ncm not in seen:
                seen.add(ncm)
                unique_data.append(entry)
            else:
                duplicates += 1
        
        self.ncm_data = unique_data
        
        if duplicates > 0:
            logger.info(f"Removed {duplicates} duplicate NCM codes")
        
        return duplicates
    
    def validate_ncm_codes(self) -> bool:
        """
        Validate all NCM codes are 8 digits.
        
        Returns:
            bool: True if all valid
        """
        invalid_count = 0
        
        for entry in self.ncm_data:
            ncm = entry['ncm']
            if not ncm.isdigit() or len(ncm) != 8:
                logger.warning(f"Invalid NCM: {ncm}")
                invalid_count += 1
        
        if invalid_count > 0:
            logger.error(f"Found {invalid_count} invalid NCM codes")
            return False
        
        logger.info("All NCM codes are valid (8 digits)")
        return True
    
    def save_to_csv(self) -> bool:
        """
        Save processed NCM data to CSV file.
        
        Returns:
            bool: True if successful
        """
        logger.info(f"Saving {len(self.ncm_data)} NCM codes to: {self.output_path}")
        
        try:
            # Create output directory if needed
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['ncm', 'description', 'ipi_rate'])
                writer.writeheader()
                
                for entry in self.ncm_data:
                    writer.writerow(entry)
            
            logger.info(f"✅ Successfully saved NCM table to: {self.output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving CSV: {e}")
            return False
    
    def print_statistics(self):
        """Print statistics about NCM table."""
        logger.info("\n" + "=" * 60)
        logger.info("NCM Table Statistics")
        logger.info("=" * 60)
        logger.info(f"Total NCM codes: {len(self.ncm_data)}")
        
        # Count by chapter (first 2 digits)
        chapters: Dict[str, int] = {}
        for entry in self.ncm_data:
            chapter = entry['ncm'][:2]
            chapters[chapter] = chapters.get(chapter, 0) + 1
        
        logger.info(f"Number of chapters: {len(chapters)}")
        logger.info(f"Average codes per chapter: {len(self.ncm_data) / len(chapters):.1f}")
        
        # Show top 5 chapters
        top_chapters = sorted(chapters.items(), key=lambda x: x[1], reverse=True)[:5]
        logger.info("\nTop 5 chapters by number of codes:")
        for chapter, count in top_chapters:
            logger.info(f"  Chapter {chapter}: {count} codes")
        
        # Count with IPI rate
        with_ipi = sum(1 for e in self.ncm_data if e.get('ipi_rate'))
        logger.info(f"\nNCM codes with IPI rate: {with_ipi} ({with_ipi/len(self.ncm_data)*100:.1f}%)")
        
        logger.info("=" * 60 + "\n")


def create_sample_ncm_csv(output_path: Path):
    """
    Create a sample NCM CSV file for demonstration.
    
    This creates a larger sample with ~100 NCM codes across different chapters.
    
    Args:
        output_path: Path where to save sample file
    """
    logger.info(f"Creating expanded sample NCM CSV at: {output_path}")
    
    # Expanded sample with NCM codes from multiple chapters
    sample_ncms = [
        # Chapter 01 - Live animals
        ("01012100", "Cavalos vivos", "0"),
        ("01022100", "Bovinos reprodutores de raça pura", "0"),
        ("01051100", "Galos e galinhas, de peso não superior a 185 g", "0"),
        
        # Chapter 02 - Meat
        ("02011000", "Carcaças e meias-carcaças de bovinos, frescas ou refrigeradas", "0"),
        ("02032900", "Carnes de suínos, congeladas", "0"),
        
        # Chapter 03 - Fish
        ("03021100", "Trutas vivas", "0"),
        ("03037800", "Merluza-do-cabo, fresca ou refrigerada", "0"),
        
        # Chapter 04 - Dairy
        ("04011000", "Leite com teor de matérias gordas não superior a 1%, em peso", "0"),
        ("04021000", "Leite em pó, não superior a 1,5% de matérias gordas", "0"),
        ("04051000", "Manteiga", "0"),
        
        # Chapter 07 - Vegetables
        ("07020000", "Tomates, frescos ou refrigerados", "5"),
        ("07031000", "Cebolas e chalotas", "5"),
        ("07070000", "Pepinos e pepininhos", "5"),
        
        # Chapter 08 - Fruits
        ("08030000", "Bananas, incluídas as da terra, frescas ou secas", "0"),
        ("08051000", "Laranjas", "0"),
        ("08061000", "Uvas frescas", "0"),
        
        # Chapter 09 - Coffee, tea, spices
        ("09011100", "Café não torrado, não descafeinado", "0"),
        ("09021000", "Chá verde (não fermentado)", "0"),
        ("09041100", "Pimenta do gênero Piper, não triturada nem em pó", "0"),
        
        # Chapter 10 - Cereals
        ("10011000", "Trigo duro", "0"),
        ("10059000", "Milho, exceto para semeadura", "0"),
        ("10061090", "Arroz com casca (arroz paddy), exceto para semeadura", "0"),
        
        # Chapter 15 - Fats and oils
        ("15071000", "Óleo de soja, em bruto", "0"),
        ("15111000", "Óleo de palma, em bruto", "0"),
        
        # Chapter 17 - Sugars
        ("17011100", "Açúcar de cana, em bruto", "0"),
        ("17019900", "Outros açúcares", "0"),
        
        # Chapter 19 - Prepared foods (bakery)
        ("19012000", "Misturas e pastas para a preparação de pães", "0"),
        ("19053100", "Biscoitos adicionados de edulcorantes", "0"),
        ("19054000", "Torradas, pão torrado e produtos semelhantes", "0"),
        ("19059010", "Pães industrializados", "0"),
        ("19059090", "Outros pães, bolos, biscoitos", "5"),
        
        # Chapter 20 - Preserved vegetables/fruits
        ("20011000", "Pepinos e pepininhos", "5"),
        ("20021000", "Tomates inteiros ou em pedaços", "5"),
        ("20091100", "Suco de laranja, congelado", "0"),
        
        # Chapter 21 - Miscellaneous food
        ("21011100", "Extratos, essências e concentrados de café", "0"),
        ("21069090", "Outras preparações alimentícias", "5"),
        
        # Chapter 22 - Beverages
        ("22011000", "Águas minerais e águas gaseificadas", "5"),
        ("22021000", "Águas, incluídas as águas minerais e as águas gaseificadas, adicionadas de açúcar", "20"),
        ("22029000", "Outras bebidas não alcoólicas", "10"),
        ("22030000", "Cervejas de malte", "15"),
        ("22041000", "Vinhos espumantes e vinhos espumosos", "25"),
        ("22042100", "Outros vinhos, em recipientes de capacidade não superior a 2 l", "20"),
        
        # Chapter 24 - Tobacco
        ("24011000", "Tabaco não manufaturado; desperdícios de tabaco", "15"),
        ("24022000", "Cigarros contendo tabaco", "300"),
        
        # Chapter 27 - Fuels
        ("27101100", "Gasolinas para motores", "0"),
        ("27101200", "Querosenes", "0"),
        ("27101900", "Óleos combustíveis (fuel oil)", "0"),
        
        # Chapter 28 - Chemicals
        ("28112100", "Dióxido de carbono", "5"),
        ("28182000", "Óxido de alumínio", "0"),
        
        # Chapter 30 - Pharmaceuticals
        ("30021000", "Anti-soros e outras frações do sangue", "0"),
        ("30023000", "Vacinas para medicina veterinária", "0"),
        ("30049099", "Outros medicamentos", "0"),
        
        # Chapter 33 - Cosmetics
        ("33041000", "Produtos de maquilagem para os lábios", "15"),
        ("33049900", "Outros produtos de beleza ou de maquilagem", "15"),
        ("33051000", "Xampus", "10"),
        ("33072000", "Desodorantes corporais e antiperspirantes", "15"),
        
        # Chapter 38 - Miscellaneous chemicals
        ("38089110", "Inseticidas", "5"),
        ("38089210", "Fungicidas", "5"),
        
        # Chapter 39 - Plastics
        ("39011000", "Polietileno de densidade inferior a 0,94", "5"),
        ("39021000", "Polipropileno", "5"),
        ("39023000", "Copolímeros de propileno", "5"),
        ("39076000", "Poli(tereftalato de etileno) - PET", "5"),
        
        # Chapter 40 - Rubber
        ("40011000", "Borracha natural, em formas primárias", "0"),
        ("40111000", "Pneus novos de borracha para automóveis", "5"),
        
        # Chapter 44 - Wood
        ("44071000", "Madeira serrada ou fendida longitudinalmente", "5"),
        ("44121000", "Madeira compensada (contraplacada)", "10"),
        
        # Chapter 48 - Paper
        ("48010000", "Papel-jornal, em bobinas ou em folhas", "0"),
        ("48025500", "Papel e cartão, sem revestimento", "5"),
        
        # Chapter 52 - Cotton
        ("52010000", "Algodão não cardado nem penteado", "0"),
        ("52051100", "Fios de algodão", "5"),
        
        # Chapter 61 - Apparel (knitted)
        ("61091000", "T-shirts, camisetas e camisas interiores", "15"),
        ("61099000", "T-shirts e camisetas de outras matérias têxteis", "15"),
        ("61101100", "Suéteres (malhas)", "15"),
        ("61121100", "Agasalhos de algodão", "15"),
        
        # Chapter 62 - Apparel (not knitted)
        ("62011100", "Sobretudos, japonas, gabões", "15"),
        ("62034100", "Calças de algodão", "15"),
        ("62052000", "Camisas de algodão, para homens ou rapazes", "15"),
        
        # Chapter 63 - Textile articles
        ("63012000", "Cobertores de fibras sintéticas", "10"),
        ("63021000", "Roupa de cama, de malha", "15"),
        
        # Chapter 64 - Footwear
        ("64029100", "Calçado com sola exterior e parte superior de borracha ou plástico", "15"),
        ("64039900", "Outro calçado", "15"),
        
        # Chapter 69 - Ceramic
        ("69072100", "Ladrilhos e placas (lajes), para pavimentação ou revestimento", "5"),
        ("69111000", "Artigos de uso doméstico", "10"),
        
        # Chapter 70 - Glass
        ("70051000", "Vidro flotado e vidro desbastado ou polido em uma ou em ambas as faces", "5"),
        ("70139900", "Outros artigos de vidro", "10"),
        
        # Chapter 73 - Iron and steel
        ("73011000", "Estacas-pranchas de ferro ou aço", "5"),
        ("73021000", "Trilhos de ferro ou aço", "0"),
        ("73181100", "Tirafundos de ferro ou aço", "10"),
        
        # Chapter 84 - Machinery
        ("84131100", "Bombas para distribuição de combustíveis", "5"),
        ("84143011", "Compressores de ar para refrigeração", "0"),
        ("84145100", "Ventiladores de mesa, de pé, de parede, de teto", "10"),
        ("84151000", "Máquinas e aparelhos de ar-condicionado", "5"),
        ("84182100", "Refrigeradores domésticos de compressão", "5"),
        ("84713012", "Microcomputadores portáteis (notebooks, laptops)", "0"),
        ("84714100", "Máquinas automáticas para processamento de dados, portáteis", "0"),
        
        # Chapter 85 - Electrical equipment
        ("85011010", "Motores elétricos de corrente alternada", "5"),
        ("85044010", "Carregadores de acumuladores", "0"),
        ("85071000", "Acumuladores elétricos de chumbo", "5"),
        ("85131000", "Lanternas elétricas portáteis", "10"),
        ("85161011", "Aquecedores elétricos de água", "5"),
        ("85165000", "Fornos de micro-ondas", "10"),
        ("85166000", "Outros fornos; fogareiros (incluídas as chapas de cocção)", "15"),
        ("85167100", "Aparelhos para preparação de café ou chá", "15"),
        ("85167200", "Torradeiras de pão", "15"),
        ("85171231", "Telefones celulares", "12"),
        ("85176255", "Aparelhos receptores para radiotelefonia ou radiotelegrafia", "15"),
        ("85182100", "Alto-falantes múltiplos montados na mesma caixa", "10"),
        ("85182200", "Alto-falantes simples montados nas suas caixas acústicas", "10"),
        ("85183000", "Fones de ouvido, auriculares", "10"),
        
        # Chapter 87 - Vehicles
        ("87032310", "Automóveis com motor a explosão, cilindrada superior a 1000 cm³", "25"),
        ("87060010", "Chassis com motor para veículos automóveis", "5"),
        ("87081000", "Para-choques e suas partes", "10"),
        ("87082990", "Outras partes e acessórios de carroçarias", "10"),
        
        # Chapter 90 - Optical instruments
        ("90041000", "Óculos de sol", "10"),
        ("90049000", "Outros óculos", "10"),
        
        # Chapter 94 - Furniture
        ("94011000", "Assentos dos tipos utilizados em veículos aéreos", "10"),
        ("94016100", "Assentos com armação de madeira, estofados", "15"),
        ("94017100", "Assentos com armação de metal, estofados", "15"),
        ("94035000", "Móveis de madeira, dos tipos utilizados em quartos de dormir", "10"),
        ("94036000", "Outros móveis de madeira", "10"),
        
        # Chapter 95 - Toys
        ("95030010", "Triciclos, patinetes e outros brinquedos de rodas", "30"),
        ("95030090", "Outros brinquedos", "20"),
        
        # Chapter 96 - Miscellaneous
        ("96081000", "Canetas esferográficas", "10"),
        ("96091000", "Lápis", "5"),
    ]
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ncm', 'description', 'ipi_rate'])
        writer.writerows(sample_ncms)
    
    logger.info(f"✅ Created expanded sample with {len(sample_ncms)} NCM codes")
    logger.info(f"   Saved to: {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Download and process NCM table')
    parser.add_argument(
        '--source',
        choices=['tipi', 'manual', 'sample'],
        default='sample',
        help='Source for NCM data (default: sample)'
    )
    parser.add_argument(
        '--input',
        type=Path,
        help='Path to manually downloaded CSV or Excel file'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('data/ncm_codes.csv'),
        help='Output path for ncm_codes.csv (default: data/ncm_codes.csv)'
    )
    
    args = parser.parse_args()
    
    # Create sample mode
    if args.source == 'sample':
        create_sample_ncm_csv(args.output)
        return 0
    
    # Initialize downloader
    downloader = NCMTableDownloader(args.output)
    
    # Process based on source
    success = False
    
    if args.source == 'tipi':
        success = downloader.download_from_tipi_pdf()
    
    elif args.source == 'manual':
        if not args.input:
            logger.error("--input required when using --source manual")
            logger.info("Example: python scripts/download_ncm_table.py --source manual --input tipi.csv")
            return 1
        
        # Detect file type
        if args.input.suffix.lower() in ['.xlsx', '.xls']:
            success = downloader.process_manual_excel(args.input)
        else:
            success = downloader.process_manual_csv(args.input)
    
    if not success:
        logger.error("Failed to download/process NCM table")
        return 1
    
    # Remove duplicates
    downloader.remove_duplicates()
    
    # Validate
    if not downloader.validate_ncm_codes():
        logger.error("Validation failed")
        return 1
    
    # Print statistics
    downloader.print_statistics()
    
    # Save to CSV
    if not downloader.save_to_csv():
        logger.error("Failed to save NCM table")
        return 1
    
    logger.info("\n✅ NCM table successfully processed!")
    logger.info(f"   File: {args.output}")
    logger.info(f"   Total codes: {len(downloader.ncm_data)}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
