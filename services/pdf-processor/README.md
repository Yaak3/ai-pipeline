# pdf-processor

Microserviço que lê PDFs do S3 (RustFS), extrai texto (nativo + OCR), limpa e salva o resultado em outro bucket.

## Camadas

- `domain/` — entidades e regras de limpeza (Python puro)
- `application/` — portas (interfaces) e caso de uso
- `adapters/inbound/` — quem dispara o caso de uso (CLI, depois HTTP/fila)
- `adapters/outbound/` — implementações concretas (boto3, PyMuPDF, Tesseract)
- `bootstrap.py` — monta tudo (composition root)

Dependências apontam sempre para dentro: `adapters -> application -> domain`.

## Comandos

```bash
uv sync
uv run pytest
uv run pdf-processor
```
