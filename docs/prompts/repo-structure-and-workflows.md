# Docs-to-Code Repository Structure & Workflows

> **Version:** 1.0.0
> **Updated:** 2025-12-31
> **Purpose:** Production GitHub repository structure for spec-driven code generation

---

## Repository Structure

```
pulser-agent-framework/
├── .github/
│   ├── workflows/
│   │   ├── docs2code-validate.yml      # Validate spec changes
│   │   ├── docs2code-breaking.yml      # Detect breaking changes
│   │   ├── docs2code-generate.yml      # Generate code from specs
│   │   └── docs2code-release.yml       # Release generated packages
│   ├── CODEOWNERS
│   └── pull_request_template.md
│
├── docs/
│   ├── specs/                           # Specification documents
│   │   ├── modules/                     # Odoo module specifications
│   │   │   ├── ipai_bir_forms.md
│   │   │   ├── ipai_close_manager.md
│   │   │   └── ipai_sod_audit.md
│   │   ├── apis/                        # API specifications
│   │   │   ├── knowledge-api.yaml       # OpenAPI 3.1
│   │   │   └── codegen-api.yaml
│   │   └── schemas/                     # Shared schemas
│   │       ├── common.yaml
│   │       └── errors.yaml
│   │
│   ├── prds/                            # Product Requirements Docs
│   │   ├── close-manager-prd.md
│   │   └── docs2code-platform-prd.md
│   │
│   ├── prompts/                         # System prompts
│   │   ├── docs-to-code-pipeline-v1.md
│   │   └── repo-structure-and-workflows.md
│   │
│   └── catalogs/                        # Resource catalogs
│       ├── ERIC_VYACHESLAV_AI_ML_CATALOG.md
│       └── MICROSOFT_AGENT_FRAMEWORK_CATALOG.md
│
├── generated/                           # AUTO-GENERATED code output
│   ├── python/                          # Python SDK
│   │   ├── ipai_sdk/
│   │   │   ├── __init__.py
│   │   │   ├── models/
│   │   │   └── client.py
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   ├── typescript/                      # TypeScript SDK
│   │   ├── src/
│   │   │   ├── models/
│   │   │   ├── client.ts
│   │   │   └── index.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   └── protobuf/                        # Protobuf definitions
│       ├── ipai/
│       │   └── v1/
│       │       ├── common.proto
│       │       └── knowledge.proto
│       └── buf.yaml
│
├── odoo/
│   └── custom_addons/                   # Odoo modules (generated + manual)
│       ├── ipai_bir_forms/
│       ├── ipai_close_manager/
│       └── ipai_sod_audit/
│
├── scripts/
│   └── docs2code/
│       ├── generate.py                  # Main generation script
│       ├── validate.py                  # Spec validation
│       ├── diff.py                      # Breaking change detection
│       └── templates/                   # Code templates
│           ├── odoo_module/
│           ├── fastapi_endpoint/
│           └── typescript_client/
│
├── skills/                              # Claude skills
│   └── docs2code/
│       ├── SKILL.md
│       ├── examples/
│       └── eval/
│
├── tools/
│   ├── openapi-generator/               # OpenAPI Generator configs
│   │   ├── python.yaml
│   │   └── typescript-fetch.yaml
│   │
│   ├── buf/                             # Buf (Protobuf) configs
│   │   ├── buf.yaml
│   │   └── buf.gen.yaml
│   │
│   └── graphql-codegen/                 # GraphQL Codegen configs
│       └── codegen.yaml
│
├── docker/
│   ├── docker-compose.dev.yml           # Local dev environment
│   └── services/
│       ├── swagger-ui/
│       ├── redoc/
│       └── prism/                       # Mock server
│
├── Makefile                             # Common commands
├── stack.yaml                           # Technology stack manifest
└── README.md
```

---

## GitHub Actions Workflows

### 1. Validate Workflow (`docs2code-validate.yml`)

Runs on every PR that touches specification files.

```yaml
name: Docs2Code Validate

on:
  push:
    paths:
      - 'docs/specs/**'
      - 'docs/prds/**'
  pull_request:
    paths:
      - 'docs/specs/**'
      - 'docs/prds/**'

jobs:
  validate-structure:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Validate Markdown Specs
        run: |
          # Check required sections in module specs
          for file in docs/specs/modules/*.md; do
            echo "Validating: $file"
            python scripts/docs2code/validate.py --file "$file" --type module
          done

      - name: Validate OpenAPI Specs
        run: |
          npm install -g @stoplight/spectral-cli
          spectral lint docs/specs/apis/*.yaml --ruleset .spectral.yaml

      - name: Validate Protobuf
        uses: bufbuild/buf-setup-action@v1
        with:
          version: '1.28.1'

      - run: buf lint generated/protobuf

  validate-examples:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Validate Python Examples
        run: |
          pip install ruff mypy
          for file in docs/specs/**/*.md; do
            python scripts/docs2code/extract_code.py "$file" --lang python | ruff check -
          done
```

### 2. Breaking Changes Workflow (`docs2code-breaking.yml`)

Detects breaking changes in API specifications.

```yaml
name: Docs2Code Breaking Changes

on:
  pull_request:
    paths:
      - 'docs/specs/apis/**'
      - 'generated/protobuf/**'

jobs:
  detect-breaking:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: OpenAPI Breaking Changes
        uses: oasdiff/oasdiff-action/breaking@main
        with:
          base: 'origin/${{ github.base_ref }}:docs/specs/apis/knowledge-api.yaml'
          revision: 'docs/specs/apis/knowledge-api.yaml'

      - name: Protobuf Breaking Changes
        uses: bufbuild/buf-setup-action@v1
      - run: buf breaking generated/protobuf --against '.git#branch=origin/${{ github.base_ref }}'

      - name: Comment on PR
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '⚠️ **Breaking changes detected!** Please review the API changes carefully.'
            })
```

### 3. Generate Workflow (`docs2code-generate.yml`)

Generates code from specifications.

```yaml
name: Docs2Code Generate

on:
  workflow_dispatch:
    inputs:
      spec_type:
        description: 'Specification type'
        required: true
        type: choice
        options:
          - openapi
          - protobuf
          - odoo-module
          - all
      spec_path:
        description: 'Path to spec file (or "all" for type)'
        required: false
        default: 'all'

jobs:
  generate-python:
    if: inputs.spec_type == 'openapi' || inputs.spec_type == 'all'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Java (for OpenAPI Generator)
        uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '17'

      - name: Generate Python SDK
        run: |
          npx @openapitools/openapi-generator-cli generate \
            -i docs/specs/apis/knowledge-api.yaml \
            -g python \
            -o generated/python \
            -c tools/openapi-generator/python.yaml \
            --additional-properties=packageName=ipai_sdk

      - name: Validate Generated Code
        run: |
          cd generated/python
          pip install ruff mypy
          ruff check ipai_sdk/
          mypy ipai_sdk/

      - name: Create PR
        uses: peter-evans/create-pull-request@v6
        with:
          commit-message: 'chore(sdk): regenerate Python SDK'
          title: '[Docs2Code] Regenerate Python SDK'
          branch: docs2code/python-sdk-${{ github.run_number }}

  generate-typescript:
    if: inputs.spec_type == 'openapi' || inputs.spec_type == 'all'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Generate TypeScript SDK
        run: |
          npx @openapitools/openapi-generator-cli generate \
            -i docs/specs/apis/knowledge-api.yaml \
            -g typescript-fetch \
            -o generated/typescript \
            -c tools/openapi-generator/typescript-fetch.yaml

      - name: Validate Generated Code
        run: |
          cd generated/typescript
          npm install
          npm run build
          npm run lint

      - name: Create PR
        uses: peter-evans/create-pull-request@v6
        with:
          commit-message: 'chore(sdk): regenerate TypeScript SDK'
          title: '[Docs2Code] Regenerate TypeScript SDK'
          branch: docs2code/typescript-sdk-${{ github.run_number }}

  generate-protobuf:
    if: inputs.spec_type == 'protobuf' || inputs.spec_type == 'all'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Buf
        uses: bufbuild/buf-setup-action@v1

      - name: Generate from Protobuf
        run: buf generate generated/protobuf

      - name: Create PR
        uses: peter-evans/create-pull-request@v6
        with:
          commit-message: 'chore(proto): regenerate from protobuf'
          title: '[Docs2Code] Regenerate Protobuf outputs'
          branch: docs2code/protobuf-${{ github.run_number }}

  generate-odoo:
    if: inputs.spec_type == 'odoo-module' || inputs.spec_type == 'all'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Dependencies
        run: pip install anthropic pyyaml jinja2

      - name: Generate Odoo Modules
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python scripts/docs2code/generate.py \
            --type odoo \
            --specs docs/specs/modules/*.md \
            --output odoo/custom_addons/

      - name: Create PR
        uses: peter-evans/create-pull-request@v6
        with:
          commit-message: 'feat(odoo): regenerate modules from specs'
          title: '[Docs2Code] Regenerate Odoo modules'
          branch: docs2code/odoo-${{ github.run_number }}
```

### 4. Release Workflow (`docs2code-release.yml`)

Publishes generated packages.

```yaml
name: Docs2Code Release

on:
  push:
    tags:
      - 'sdk-python-v*'
      - 'sdk-typescript-v*'

jobs:
  release-python:
    if: startsWith(github.ref, 'refs/tags/sdk-python-v')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Build Package
        run: |
          cd generated/python
          pip install build
          python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          packages-dir: generated/python/dist/

  release-typescript:
    if: startsWith(github.ref, 'refs/tags/sdk-typescript-v')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          registry-url: 'https://registry.npmjs.org'

      - name: Build & Publish
        run: |
          cd generated/typescript
          npm install
          npm run build
          npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

---

## OpenAPI Generator Configs

### Python Config (`tools/openapi-generator/python.yaml`)

```yaml
# OpenAPI Generator configuration for Python SDK
additionalProperties:
  packageName: ipai_sdk
  projectName: ipai-sdk
  packageVersion: 1.0.0
  pythonAttrNoneIfUnset: true
  generateSourceCodeOnly: false
  library: urllib3
  useNose: false
  useDatetime: true

files:
  .gitignore:
    templateType: SupportingFiles
    destinationFilename: .gitignore
  pyproject.toml:
    templateType: SupportingFiles
    destinationFilename: pyproject.toml

typeMappings:
  DateTime: datetime.datetime
  Date: datetime.date

importMappings:
  datetime: datetime.datetime
```

### TypeScript Config (`tools/openapi-generator/typescript-fetch.yaml`)

```yaml
# OpenAPI Generator configuration for TypeScript SDK
additionalProperties:
  npmName: "@insightpulseai/sdk"
  npmVersion: 1.0.0
  supportsES6: true
  withInterfaces: true
  typescriptThreePlus: true
  useSingleRequestParameter: true

files:
  package.json:
    templateType: SupportingFiles
    destinationFilename: package.json
  tsconfig.json:
    templateType: SupportingFiles
    destinationFilename: tsconfig.json
```

---

## Buf Configuration

### `generated/protobuf/buf.yaml`

```yaml
version: v1
name: buf.build/insightpulseai/ipai
breaking:
  use:
    - FILE
lint:
  use:
    - DEFAULT
  except:
    - PACKAGE_VERSION_SUFFIX
  rpc_allow_same_request_response: true
  service_suffix: Service
```

### `tools/buf/buf.gen.yaml`

```yaml
version: v1
managed:
  enabled: true
  go_package_prefix:
    default: github.com/insightpulseai/pulser-agent-framework/generated/go
plugins:
  - plugin: buf.build/protocolbuffers/python
    out: generated/python/ipai_sdk/proto
  - plugin: buf.build/grpc/python
    out: generated/python/ipai_sdk/proto
  - plugin: buf.build/community/nipunn1313-mypy
    out: generated/python/ipai_sdk/proto
  - plugin: buf.build/protocolbuffers/es
    out: generated/typescript/src/proto
    opt:
      - target=ts
```

---

## Docker Compose (Local Dev)

### `docker/docker-compose.dev.yml`

```yaml
version: '3.8'

services:
  swagger-ui:
    image: swaggerapi/swagger-ui:latest
    ports:
      - "8080:8080"
    environment:
      SWAGGER_JSON: /specs/knowledge-api.yaml
    volumes:
      - ../docs/specs/apis:/specs:ro

  redoc:
    image: redocly/redoc:latest
    ports:
      - "8081:80"
    environment:
      SPEC_URL: /specs/knowledge-api.yaml
    volumes:
      - ../docs/specs/apis:/usr/share/nginx/html/specs:ro

  prism:
    image: stoplight/prism:4
    ports:
      - "4010:4010"
    command: mock -h 0.0.0.0 /specs/knowledge-api.yaml
    volumes:
      - ../docs/specs/apis:/specs:ro

  buf-studio:
    image: bufbuild/buf:latest
    ports:
      - "8082:8082"
    working_dir: /workspace
    volumes:
      - ../generated/protobuf:/workspace
    command: ["studio", "--port", "8082"]
```

---

## Makefile

```makefile
# =============================================================================
# Docs-to-Code Pipeline Commands
# =============================================================================

.PHONY: help validate generate clean dev-server

help:
	@echo "Docs-to-Code Pipeline Commands:"
	@echo "  make validate        - Validate all specifications"
	@echo "  make generate        - Generate all code from specs"
	@echo "  make generate-python - Generate Python SDK only"
	@echo "  make generate-ts     - Generate TypeScript SDK only"
	@echo "  make generate-odoo   - Generate Odoo modules only"
	@echo "  make dev-server      - Start local dev servers"
	@echo "  make clean           - Remove generated files"

# -----------------------------------------------------------------------------
# Validation
# -----------------------------------------------------------------------------
validate: validate-openapi validate-proto validate-markdown

validate-openapi:
	@echo "Validating OpenAPI specs..."
	npx @stoplight/spectral-cli lint docs/specs/apis/*.yaml

validate-proto:
	@echo "Validating Protobuf..."
	cd generated/protobuf && buf lint

validate-markdown:
	@echo "Validating Markdown specs..."
	python scripts/docs2code/validate.py --all

# -----------------------------------------------------------------------------
# Code Generation
# -----------------------------------------------------------------------------
generate: generate-python generate-ts generate-proto

generate-python:
	@echo "Generating Python SDK..."
	npx @openapitools/openapi-generator-cli generate \
		-i docs/specs/apis/knowledge-api.yaml \
		-g python \
		-o generated/python \
		-c tools/openapi-generator/python.yaml

generate-ts:
	@echo "Generating TypeScript SDK..."
	npx @openapitools/openapi-generator-cli generate \
		-i docs/specs/apis/knowledge-api.yaml \
		-g typescript-fetch \
		-o generated/typescript \
		-c tools/openapi-generator/typescript-fetch.yaml

generate-proto:
	@echo "Generating from Protobuf..."
	buf generate generated/protobuf

generate-odoo:
	@echo "Generating Odoo modules..."
	python scripts/docs2code/generate.py --type odoo --specs docs/specs/modules/*.md

# -----------------------------------------------------------------------------
# Development
# -----------------------------------------------------------------------------
dev-server:
	@echo "Starting dev servers..."
	docker-compose -f docker/docker-compose.dev.yml up -d
	@echo "Swagger UI: http://localhost:8080"
	@echo "Redoc: http://localhost:8081"
	@echo "Prism Mock: http://localhost:4010"

dev-stop:
	docker-compose -f docker/docker-compose.dev.yml down

# -----------------------------------------------------------------------------
# Cleanup
# -----------------------------------------------------------------------------
clean:
	rm -rf generated/python/ipai_sdk/*.py
	rm -rf generated/typescript/src/*.ts
	rm -rf generated/go/
	@echo "Generated files cleaned"
```

---

## Key Repository Links

| Tool | Purpose | Repository |
|------|---------|------------|
| **OpenAPI Generator** | Generate SDKs from OpenAPI | [github.com/OpenAPITools/openapi-generator](https://github.com/OpenAPITools/openapi-generator) |
| **Buf** | Protobuf tooling | [github.com/bufbuild/buf](https://github.com/bufbuild/buf) |
| **GraphQL Codegen** | Generate from GraphQL | [github.com/dotansimha/graphql-code-generator](https://github.com/dotansimha/graphql-code-generator) |
| **Spectral** | OpenAPI linting | [github.com/stoplightio/spectral](https://github.com/stoplightio/spectral) |
| **Prism** | Mock servers | [github.com/stoplightio/prism](https://github.com/stoplightio/prism) |

---

*Part of the InsightPulseAI Docs-to-Code Pipeline*
*See also: docs-to-code-pipeline-v1.md, skills/docs2code/SKILL.md*
