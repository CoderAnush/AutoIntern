# Elasticsearch Indexing

The worker indexes jobs into Elasticsearch index `autointern-jobs`.

Index template (worker)
- The worker ensures the index exists before indexing a document.
- Current mapping:
  - `id`: keyword
  - `external_id`: keyword
  - `title`: text
  - `description`: text
  - `location`: keyword
  - `source`: keyword

Why this matters
- Keyword fields (`external_id`, `source`, `location`) enable exact matching and aggregations.
- Text fields (`title`, `description`) enable full-text search and ranking.

Production recommendations
- Create an index template via infrastructure (Terraform/Ansible) or an init job before workers start.
- Add analyzers for skills and location normalization if needed.
- Use ILM (index lifecycle management) for retention and cost control when the dataset grows.

Validation
- The E2E test polls Elasticsearch for the document after worker processing.
- Use `GET http://localhost:9200/autointern-jobs/_search?q=external_id:<id>` to verify indexing.
