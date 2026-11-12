"""Entidades do domínio: Document e Page.

Regra: este módulo NÃO importa nada fora da biblioteca padrão.
"""

from dataclasses import dataclass, replace
from enum import Enum

DEFAULT_MIN_CHARS_FOR_NATIVE_TEXT = 50


class TextSource(Enum):
    """De onde veio o texto da página."""

    NATIVE = "native"  # extraído direto do PDF
    OCR = "ocr"  # reconhecido a partir da imagem da página


@dataclass(frozen=True)
class Page:
    number: int
    text: str
    source: TextSource = TextSource.NATIVE

    def __post_init__(self) -> None:

        if self.number < 1:
            raise ValueError("Número de pagina tem que ser maior que zero")

    def needs_ocr(self, min_chars: int = DEFAULT_MIN_CHARS_FOR_NATIVE_TEXT) -> bool:
        """Regra de negócio: página com pouco texto nativo provavelmente é escaneada.

        Espaços e quebras de linha não contam como caracteres.
        Página que já passou pelo OCR nunca precisa de OCR de novo.
        """
        if self.source is TextSource.OCR:
            return False

        return len(self.text.strip()) < min_chars

    def with_ocr_text(self, text: str) -> "Page":
        """Retorna uma nova página com o texto vindo do OCR.

        Garante que texto e origem mudem juntos: texto de OCR sempre fica
        marcado como TextSource.OCR. A página original não é alterada.
        """
        return replace(self, text=text, source=TextSource.OCR)


@dataclass(frozen=True)
class Document:
    name: str
    extension: str
    pages: tuple[Page, ...]

    def __post_init__(self) -> None:
        if not self.pages:
            raise ValueError("Documento criado sem paginas")

    @property
    def num_pages(self) -> int:
        return len(self.pages)

    @property
    def full_text(self) -> str:
        return "\n".join(page.text for page in self.pages)

    def get_page_text(self, page_number: int) -> str | None:
        for page in self.pages:
            if page.number == page_number:
                return page.text

        return None
