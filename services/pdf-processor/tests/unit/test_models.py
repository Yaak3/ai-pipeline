"""Testes unitários do domínio: Page, TextSource e Document."""

from dataclasses import FrozenInstanceError

import pytest

from pdf_processor.domain.models import (
    DEFAULT_MIN_CHARS_FOR_NATIVE_TEXT,
    Document,
    Page,
    TextSource,
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def make_document(*texts: str) -> Document:
    """Cria um Document com uma página para cada texto, numeradas a partir de 1."""
    pages = tuple(Page(number=i, text=text) for i, text in enumerate(texts, start=1))
    return Document(name="relatorio", extension="pdf", pages=pages)


# --------------------------------------------------------------------------- #
# Page: criação e validação
# --------------------------------------------------------------------------- #


class TestPageCreation:
    def test_cria_pagina_valida(self) -> None:
        page = Page(number=1, text="conteúdo")

        assert page.number == 1
        assert page.text == "conteúdo"

    def test_origem_padrao_e_native(self) -> None:
        page = Page(number=1, text="conteúdo")

        assert page.source is TextSource.NATIVE

    def test_aceita_pagina_sem_texto(self) -> None:
        # Página escaneada chega do extrator sem texto nativo.
        page = Page(number=1, text="")

        assert page.text == ""

    @pytest.mark.parametrize("number", [0, -1, -100])
    def test_numero_menor_que_um_da_erro(self, number: int) -> None:
        with pytest.raises(ValueError, match="maior que zero"):
            Page(number=number, text="conteúdo")

    def test_pagina_e_imutavel(self) -> None:
        page = Page(number=1, text="conteúdo")

        with pytest.raises(FrozenInstanceError):
            page.text = "outro"  # type: ignore[misc]


# --------------------------------------------------------------------------- #
# Page.needs_ocr
# --------------------------------------------------------------------------- #


class TestPageNeedsOcr:
    def test_limite_padrao_e_50(self) -> None:
        assert DEFAULT_MIN_CHARS_FOR_NATIVE_TEXT == 50

    def test_pagina_vazia_precisa_de_ocr(self) -> None:
        assert Page(number=1, text="").needs_ocr() is True

    def test_pagina_com_menos_do_que_o_limite_precisa_de_ocr(self) -> None:
        assert Page(number=1, text="x" * 49).needs_ocr() is True

    def test_pagina_exatamente_no_limite_nao_precisa_de_ocr(self) -> None:
        assert Page(number=1, text="x" * 50).needs_ocr() is False

    def test_pagina_com_mais_do_que_o_limite_nao_precisa_de_ocr(self) -> None:
        assert Page(number=1, text="x" * 500).needs_ocr() is False

    @pytest.mark.parametrize("text", ["   ", "\n\n\n", " \t \n "])
    def test_espacos_e_quebras_de_linha_nao_contam(self, text: str) -> None:
        assert Page(number=1, text=text).needs_ocr() is True

    def test_espacos_ao_redor_nao_contam_para_o_limite(self) -> None:
        # 49 caracteres reais + espaços em volta continua abaixo do limite.
        page = Page(number=1, text="   " + "x" * 49 + "\n\n")

        assert page.needs_ocr() is True

    def test_aceita_limite_customizado(self) -> None:
        page = Page(number=1, text="abc")

        assert page.needs_ocr(min_chars=3) is False
        assert page.needs_ocr(min_chars=4) is True

    def test_pagina_ocr_nunca_precisa_de_ocr(self) -> None:
        page = Page(number=1, text="", source=TextSource.OCR)

        assert page.needs_ocr() is False

    def test_pagina_ocr_com_texto_curto_nao_precisa_de_ocr_de_novo(self) -> None:
        page = Page(number=1, text="").with_ocr_text("curto")

        assert page.needs_ocr() is False


# --------------------------------------------------------------------------- #
# Page.with_ocr_text
# --------------------------------------------------------------------------- #


class TestPageWithOcrText:
    def test_troca_texto_e_marca_origem_como_ocr(self) -> None:
        page = Page(number=3, text="").with_ocr_text("texto reconhecido")

        assert page.text == "texto reconhecido"
        assert page.source is TextSource.OCR

    def test_mantem_o_numero_da_pagina(self) -> None:
        page = Page(number=3, text="").with_ocr_text("texto reconhecido")

        assert page.number == 3

    def test_nao_altera_a_pagina_original(self) -> None:
        original = Page(number=3, text="")

        original.with_ocr_text("texto reconhecido")

        assert original.text == ""
        assert original.source is TextSource.NATIVE

    def test_retorna_um_objeto_novo(self) -> None:
        original = Page(number=3, text="")

        assert original.with_ocr_text("texto") is not original


# --------------------------------------------------------------------------- #
# Document
# --------------------------------------------------------------------------- #


class TestDocumentCreation:
    def test_cria_documento_valido(self) -> None:
        document = make_document("um", "dois")

        assert document.name == "relatorio"
        assert document.extension == "pdf"
        assert len(document.pages) == 2

    def test_documento_sem_paginas_da_erro(self) -> None:
        with pytest.raises(ValueError, match="sem paginas"):
            Document(name="vazio", extension="pdf", pages=())

    def test_documento_e_imutavel(self) -> None:
        document = make_document("um")

        with pytest.raises(FrozenInstanceError):
            document.name = "outro"  # type: ignore[misc]


class TestDocumentNumPages:
    @pytest.mark.parametrize("quantidade", [1, 2, 10])
    def test_conta_as_paginas(self, quantidade: int) -> None:
        document = make_document(*["texto"] * quantidade)

        assert document.num_pages == quantidade


class TestDocumentFullText:
    def test_uma_pagina_retorna_o_proprio_texto(self) -> None:
        assert make_document("único").full_text == "único"

    def test_junta_paginas_com_quebra_de_linha_na_ordem(self) -> None:
        document = make_document("primeira", "segunda", "terceira")

        assert document.full_text == "primeira\nsegunda\nterceira"

    def test_nao_deixa_quebra_de_linha_sobrando_no_fim(self) -> None:
        assert not make_document("um", "dois").full_text.endswith("\n")


class TestDocumentGetPageText:
    def test_retorna_texto_da_pagina_pelo_numero(self) -> None:
        document = make_document("primeira", "segunda")

        assert document.get_page_text(1) == "primeira"
        assert document.get_page_text(2) == "segunda"

    @pytest.mark.parametrize("numero", [0, 3, 99])
    def test_pagina_inexistente_retorna_none(self, numero: int) -> None:
        document = make_document("primeira", "segunda")

        assert document.get_page_text(numero) is None
