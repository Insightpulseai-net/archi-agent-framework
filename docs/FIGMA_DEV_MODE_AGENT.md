# Figma Dev Mode-Aware Coding Agent

**Purpose**: Automate design-to-code workflows using Figma Dev Mode as the source of truth for UI implementation, visual parity testing, and design system synchronization.

**Stack Integration**: Supabase PostgreSQL 17.6 | Vercel Next.js 14 | Figma MCP Server (port 3845) | Visual Parity Gates (SSIM ≥0.97 mobile, ≥0.98 desktop)

---

## Core Principles

### 1. Dev Mode as Trusted Surface
- **Only parse frames/components marked "Ready for dev"** in Figma Dev Mode
- Ignore everything else (sketches, exploration, work-in-progress)
- Use "Last edited" timestamps to detect staleness and trigger updates

### 2. Code Connect over Auto-Generated Code
- **Prefer Code Connect snippets** (real design system code) over generic auto-generated code
- Map Figma components → actual React/Tailwind components in codebase
- Propagate component changes via dev resources (GitHub links, Storybook URLs)

### 3. Annotation-Driven Development
- **Parse Figma annotations** for business logic, validation rules, RLS policies
- Treat annotations as single source of truth for edge cases and constraints
- Example: "This field requires RLS tenant_id isolation" → auto-generate RLS policy

### 4. Visual Parity Enforcement
- **SSIM thresholds** are non-negotiable: ≥0.97 mobile (375×812), ≥0.98 desktop (1920×1080)
- Figma frames marked "Ready for dev" → baseline screenshots
- Status change to "In QA" → trigger visual regression tests

---

## Agent Capabilities

### Capability 1: Visual Parity Gate Automation

**Trigger**: Figma frame status changes to "Ready for dev"

**Workflow**:
1. **Detect Status Change** (via Figma webhook or polling)
2. **Fetch Frame** via Figma MCP API:
   ```typescript
   // MCP tool call
   {
     "tool": "figma_get_ready_frames",
     "params": {
       "file_id": "ABC123XYZ",
       "filter": "ready_for_dev"
     }
   }
   // Returns: [
   //   { id: "123:456", name: "BIR Status Dashboard", last_edited: "2025-12-09T10:30:00Z" },
   //   { id: "789:012", name: "OCR Confidence Dashboard", last_edited: "2025-12-08T14:20:00Z" }
   // ]
   ```

3. **Export Frame as PNG** (baseline screenshot):
   ```typescript
   {
     "tool": "figma_export_frame",
     "params": {
       "file_id": "ABC123XYZ",
       "node_id": "123:456",
       "format": "png",
       "scale": 2,  // Retina
       "viewport": { "width": 1920, "height": 1080 }  // Desktop
     }
   }
   ```

4. **Store Baseline** in Supabase:
   ```sql
   INSERT INTO visual_baseline (route, viewport, baseline_url, figma_node_id, created_at)
   VALUES (
     '/dashboard/bir-status',
     'desktop',
     'https://spdtwktxdalcfigzeqrz.supabase.co/storage/v1/object/public/baselines/bir-status-desktop.png',
     '123:456',
     NOW()
   );
   ```

5. **Generate Comparison Script**:
   ```bash
   # scripts/snap-from-figma.js
   node scripts/ssim.js \
     --baseline supabase://baselines/bir-status-desktop.png \
     --current https://archi-agent-framework.vercel.app/dashboard/bir-status \
     --viewport 1920x1080 \
     --threshold 0.98
   ```

**Expected Outcome**: SSIM score ≥0.98 or deployment blocked

---

### Capability 2: Dashboard Code Generation

**Trigger**: Figma component marked "Ready for dev" with Code Connect mapping

**Workflow**:
1. **Fetch Code Connect** for component:
   ```typescript
   {
     "tool": "figma_get_code_connect",
     "params": {
       "file_id": "ABC123XYZ",
       "node_id": "123:456",  // BIR Status Dashboard frame
       "language": "typescript"
     }
   }
   // Returns Code Connect snippet if configured, else auto-generated code
   ```

2. **Parse Component Structure**:
   - Extract layout (Grid, Flex, Stack)
   - Extract styles (colors, typography, spacing from Figma variables)
   - Extract states (hover, focus, disabled from variants)

3. **Generate Next.js Page**:
   ```typescript
   // app/dashboard/bir-status/page.tsx
   // Auto-generated from Figma "BIR Status Dashboard" frame (node_id: 123:456)
   // Last synced: 2025-12-09T10:30:00Z

   import { Card } from '@/components/ui/card';  // From Code Connect
   import { Table } from '@/components/ui/table';  // From Code Connect
   import { StatusBadge } from '@/components/ui/badge';  // From Code Connect

   export default function BIRStatusDashboard() {
     return (
       <div className="grid grid-cols-1 gap-6 p-6">
         {/* Layout extracted from Figma Auto Layout */}
         <Card>
           <Table>
             {/* Columns from Figma table component */}
             <thead>
               <tr>
                 <th>Form Type</th>
                 <th>Filing Period</th>
                 <th>Deadline</th>
                 <th>Status</th>
               </tr>
             </thead>
             <tbody>
               {/* Data fetching from Supabase silver_bir_forms */}
             </tbody>
           </Table>
         </Card>
       </div>
     );
   }
   ```

4. **Extract Figma Variables → Tailwind Config**:
   ```typescript
   {
     "tool": "figma_get_variables",
     "params": {
       "file_id": "ABC123XYZ",
       "collection_id": "VariableCollectionId:1:2"
     }
   }
   // Returns:
   // {
   //   "colors": {
   //     "primary-500": "#0066CC",
   //     "success-500": "#22C55E",
   //     "warning-500": "#F59E0B",
   //     "danger-500": "#EF4444"
   //   },
   //   "spacing": {
   //     "xs": "4px",
   //     "sm": "8px",
   //     "md": "16px",
   //     "lg": "24px"
   //   }
   // }
   ```

5. **Sync to Tailwind Config**:
   ```javascript
   // tailwind.config.js
   module.exports = {
     theme: {
       extend: {
         colors: {
           primary: { 500: '#0066CC' },  // From Figma variables
           success: { 500: '#22C55E' },
           warning: { 500: '#F59E0B' },
           danger: { 500: '#EF4444' }
         },
         spacing: {
           xs: '4px',
           sm: '8px',
           md: '16px',
           lg: '24px'
         }
       }
     }
   };
   ```

6. **Store Theme in Supabase** (for runtime access):
   ```sql
   INSERT INTO theme_tokens (source, token_type, token_name, token_value, figma_variable_id)
   VALUES
     ('figma', 'color', 'primary-500', '#0066CC', 'VariableID:1:100'),
     ('figma', 'color', 'success-500', '#22C55E', 'VariableID:1:101'),
     ('figma', 'spacing', 'md', '16px', 'VariableID:1:200');
   ```

**Expected Outcome**: Generated page matches Figma design with SSIM ≥0.98

---

### Capability 3: Annotation-Driven Development

**Trigger**: Figma annotation added to component/frame

**Workflow**:
1. **Parse Annotations** from Figma:
   ```typescript
   {
     "tool": "figma_get_annotations",
     "params": {
       "file_id": "ABC123XYZ",
       "node_id": "123:456"
     }
   }
   // Returns:
   // [
   //   {
   //     "id": "annotation-1",
   //     "type": "measurement",
   //     "text": "12px spacing between cards",
   //     "position": { "x": 100, "y": 200 }
   //   },
   //   {
   //     "id": "annotation-2",
   //     "type": "note",
   //     "text": "This table uses RLS with tenant_id isolation. Filter by app.current_tenant_id",
   //     "position": { "x": 300, "y": 400 }
   //   }
   // ]
   ```

2. **Extract Business Logic** from annotation text:
   ```typescript
   // Annotation: "This table uses RLS with tenant_id isolation. Filter by app.current_tenant_id"

   // Auto-generate RLS policy:
   const rlsPolicy = `
   CREATE POLICY "bir_forms_tenant_isolation"
   ON scout.silver_bir_forms
   FOR ALL
   USING (tenant_id = (current_setting('app.current_tenant_id')::uuid));
   `;

   // Auto-generate API filter:
   const apiFilter = `
   const { data, error } = await supabase
     .from('silver_bir_forms')
     .select('*')
     .eq('tenant_id', session.user.app_metadata.tenant_id);
   `;
   ```

3. **Extract Validation Rules**:
   ```typescript
   // Annotation: "Amount must be positive. Max 2 decimal places. Required field."

   // Auto-generate Zod schema:
   const schema = z.object({
     amount: z.number()
       .positive("Amount must be positive")
       .multipleOf(0.01, "Max 2 decimal places")
       .min(0.01, "Amount is required")
   });

   // Auto-generate SQL constraint:
   const constraint = `
   ALTER TABLE scout.silver_expenses
   ADD CONSTRAINT check_amount_positive CHECK (amount > 0);
   `;
   ```

4. **Extract State Management**:
   ```typescript
   // Annotation: "Status workflow: draft → pending → approved → filed"

   // Auto-generate state machine:
   const statusWorkflow = {
     draft: ['pending', 'cancelled'],
     pending: ['approved', 'rejected'],
     approved: ['filed'],
     rejected: ['draft'],
     filed: [],  // Terminal state
     cancelled: []  // Terminal state
   };

   // Auto-generate SQL enum:
   const statusEnum = `
   CREATE TYPE bir_status AS ENUM ('draft', 'pending', 'approved', 'rejected', 'filed', 'cancelled');
   `;
   ```

**Expected Outcome**: Business logic, validation, and state management auto-generated from annotations

---

### Capability 4: Design Token Sync (Figma ↔ Supabase ↔ Tailwind)

**Trigger**: Figma variable collection updated

**Workflow**:
1. **Fetch All Variables** from Figma:
   ```typescript
   {
     "tool": "figma_get_all_variables",
     "params": {
       "file_id": "ABC123XYZ"
     }
   }
   ```

2. **Normalize to JSON** (Design System CLI format):
   ```json
   {
     "colors": {
       "primary": {
         "50": "#E6F2FF",
         "500": "#0066CC",
         "900": "#003366"
       },
       "success": { "500": "#22C55E" },
       "warning": { "500": "#F59E0B" },
       "danger": { "500": "#EF4444" }
     },
     "typography": {
       "fontFamily": {
         "sans": ["Inter", "sans-serif"],
         "mono": ["Fira Code", "monospace"]
       },
       "fontSize": {
         "xs": "12px",
         "sm": "14px",
         "base": "16px",
         "lg": "18px",
         "xl": "20px",
         "2xl": "24px"
       },
       "fontWeight": {
         "normal": 400,
         "medium": 500,
         "semibold": 600,
         "bold": 700
       },
       "lineHeight": {
         "tight": 1.25,
         "normal": 1.5,
         "relaxed": 1.75
       }
     },
     "spacing": {
       "xs": "4px",
       "sm": "8px",
       "md": "16px",
       "lg": "24px",
       "xl": "32px",
       "2xl": "48px"
     },
     "borderRadius": {
       "none": "0",
       "sm": "4px",
       "md": "8px",
       "lg": "12px",
       "full": "9999px"
     },
     "shadows": {
       "sm": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
       "md": "0 4px 6px -1px rgb(0 0 0 / 0.1)",
       "lg": "0 10px 15px -3px rgb(0 0 0 / 0.1)"
     }
   }
   ```

3. **Store in Supabase** (theme_tokens table):
   ```sql
   CREATE TABLE theme_tokens (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     source TEXT NOT NULL,  -- 'figma', 'tailwind', 'manual'
     token_type TEXT NOT NULL,  -- 'color', 'spacing', 'typography', 'shadow'
     token_name TEXT NOT NULL,  -- 'primary-500', 'md', 'fontFamily-sans'
     token_value TEXT NOT NULL,  -- '#0066CC', '16px', '["Inter", "sans-serif"]'
     figma_variable_id TEXT,  -- Link back to Figma
     created_at TIMESTAMPTZ DEFAULT NOW(),
     updated_at TIMESTAMPTZ DEFAULT NOW(),
     UNIQUE(source, token_type, token_name)
   );

   -- Insert tokens
   INSERT INTO theme_tokens (source, token_type, token_name, token_value, figma_variable_id)
   VALUES
     ('figma', 'color', 'primary-500', '#0066CC', 'VariableID:1:100'),
     ('figma', 'spacing', 'md', '16px', 'VariableID:1:200')
   ON CONFLICT (source, token_type, token_name)
   DO UPDATE SET token_value = EXCLUDED.token_value, updated_at = NOW();
   ```

4. **Generate Tailwind Config**:
   ```javascript
   // tailwind.config.js (auto-generated from Supabase theme_tokens)
   const tokens = await supabase.from('theme_tokens').select('*');

   module.exports = {
     theme: {
       extend: {
         colors: tokens.filter(t => t.token_type === 'color').reduce((acc, t) => {
           const [group, variant] = t.token_name.split('-');
           acc[group] = acc[group] || {};
           acc[group][variant] = t.token_value;
           return acc;
         }, {}),
         spacing: tokens.filter(t => t.token_type === 'spacing').reduce((acc, t) => {
           acc[t.token_name] = t.token_value;
           return acc;
         }, {})
       }
     }
   };
   ```

5. **Sync Back to Figma** (optional - write changes from code → Figma):
   ```typescript
   // If Tailwind config manually updated, push back to Figma
   {
     "tool": "figma_update_variable",
     "params": {
       "file_id": "ABC123XYZ",
       "variable_id": "VariableID:1:100",
       "value": "#0066DD"  // Updated primary color
     }
   }
   ```

**Expected Outcome**: Design tokens synchronized across Figma, Supabase, and Tailwind with single source of truth

---

## MCP Tool Specifications

### Tool: `figma_get_ready_frames`
**Purpose**: List all frames/components marked "Ready for dev" in a Figma file

**Input**:
```typescript
{
  "file_id": string,          // Figma file ID
  "filter": "ready_for_dev" | "in_qa" | "all",  // Status filter
  "include_sections": boolean  // Include section hierarchy
}
```

**Output**:
```typescript
{
  "frames": [
    {
      "id": string,           // Node ID (e.g., "123:456")
      "name": string,         // Frame name
      "type": "FRAME" | "COMPONENT" | "SECTION",
      "status": "ready_for_dev" | "in_qa" | "in_progress",
      "last_edited": string,  // ISO 8601 timestamp
      "url": string,          // Deep link to frame
      "annotations": number,  // Count of annotations
      "measurements": number  // Count of measurements
    }
  ]
}
```

---

### Tool: `figma_export_frame`
**Purpose**: Export a frame as PNG/SVG/PDF for baseline screenshot capture

**Input**:
```typescript
{
  "file_id": string,
  "node_id": string,
  "format": "png" | "svg" | "pdf",
  "scale": number,  // 1, 2 (retina), 3, 4
  "viewport": {
    "width": number,
    "height": number
  }
}
```

**Output**:
```typescript
{
  "url": string,  // Temporary download URL (expires in 14 days)
  "size_bytes": number,
  "dimensions": { "width": number, "height": number }
}
```

---

### Tool: `figma_get_code_connect`
**Purpose**: Fetch Code Connect snippet for a component (real design system code)

**Input**:
```typescript
{
  "file_id": string,
  "node_id": string,
  "language": "typescript" | "jsx" | "swift" | "kotlin"
}
```

**Output**:
```typescript
{
  "has_code_connect": boolean,
  "snippet": string,  // Code Connect snippet if available
  "imports": string[],  // Required imports
  "props": {
    "name": string,
    "type": string,
    "default": any
  }[],
  "fallback_code": string  // Auto-generated code if no Code Connect
}
```

---

### Tool: `figma_get_annotations`
**Purpose**: Parse annotations and measurements from a frame

**Input**:
```typescript
{
  "file_id": string,
  "node_id": string,
  "types": ("measurement" | "note")[]  // Filter by type
}
```

**Output**:
```typescript
{
  "annotations": [
    {
      "id": string,
      "type": "measurement" | "note",
      "text": string,  // Annotation content
      "position": { "x": number, "y": number },
      "target_node_id": string  // Node being annotated
    }
  ]
}
```

---

### Tool: `figma_get_all_variables`
**Purpose**: Fetch all design tokens (colors, spacing, typography) from Figma variables

**Input**:
```typescript
{
  "file_id": string,
  "collection_ids": string[]  // Optional: filter by collection
}
```

**Output**:
```typescript
{
  "variables": {
    "colors": {
      [name: string]: string  // e.g., "primary-500": "#0066CC"
    },
    "spacing": {
      [name: string]: string  // e.g., "md": "16px"
    },
    "typography": {
      [name: string]: string | number | string[]
    },
    "borderRadius": {
      [name: string]: string
    },
    "shadows": {
      [name: string]: string
    }
  }
}
```

---

### Tool: `figma_subscribe_status_changes`
**Purpose**: Subscribe to webhook for status changes (Ready for dev, In QA, etc.)

**Input**:
```typescript
{
  "file_id": string,
  "webhook_url": string,  // e.g., "https://archi-agent-framework.vercel.app/api/figma-webhook"
  "events": ("status_changed" | "version_created" | "component_updated")[]
}
```

**Output**:
```typescript
{
  "webhook_id": string,
  "status": "active",
  "created_at": string
}
```

**Webhook Payload** (sent to webhook_url):
```typescript
{
  "event_type": "status_changed",
  "file_id": string,
  "node_id": string,
  "old_status": "in_progress",
  "new_status": "ready_for_dev",
  "timestamp": string,
  "user": {
    "id": string,
    "email": string
  }
}
```

---

## Integration with Phase 1 Acceptance Gates

### Gate 7: Visual Parity Thresholds (AUTOMATED)

**Before** (Manual):
```bash
# Capture baseline screenshots manually
node scripts/snap.js --routes="/expenses,/tasks" --base-url="https://localhost:3000"

# Run SSIM comparison manually
node scripts/ssim.js --routes="/expenses,/tasks" --threshold-mobile=0.97
```

**After** (Figma Dev Mode-Driven):
```bash
# 1. Designer marks frame "Ready for dev" in Figma
# 2. Webhook triggers baseline capture:

# API route: /api/figma-webhook
POST https://archi-agent-framework.vercel.app/api/figma-webhook
{
  "event_type": "status_changed",
  "node_id": "123:456",
  "new_status": "ready_for_dev"
}

# 3. Agent auto-executes:
- figma_export_frame(node_id="123:456", format="png", viewport={width:1920, height:1080})
- Upload to Supabase storage: supabase://baselines/bir-status-desktop.png
- Insert into visual_baseline table
- Generate comparison script for CI

# 4. On deploy, CI runs:
node scripts/ssim-from-figma.js --figma-node-id=123:456 --threshold=0.98
# Compares deployed UI against Figma baseline
# Blocks merge if SSIM < 0.98
```

**Acceptance Criteria**:
- ✅ All frames marked "Ready for dev" have baselines in Supabase
- ✅ SSIM ≥0.97 (mobile), ≥0.98 (desktop) for all routes
- ✅ Visual regression tests run on every PR
- ✅ Baseline updates auto-triggered on Figma status changes

---

## CI/CD Workflow (GitHub Actions)

### `.github/workflows/figma-sync.yml`

```yaml
name: Figma Dev Mode Sync

on:
  repository_dispatch:
    types: [figma_status_changed]  # Triggered by Figma webhook
  workflow_dispatch:
    inputs:
      file_id:
        description: 'Figma file ID'
        required: true
      node_id:
        description: 'Figma node ID'
        required: true

jobs:
  sync-baseline:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm install

      - name: Fetch Figma frame
        id: figma
        run: |
          # Call Figma MCP API via Node.js script
          node scripts/figma-sync.js \
            --file-id ${{ github.event.client_payload.file_id || inputs.file_id }} \
            --node-id ${{ github.event.client_payload.node_id || inputs.node_id }} \
            --action export_baseline

      - name: Upload to Supabase storage
        run: |
          npx supabase storage upload \
            baselines/${{ steps.figma.outputs.filename }} \
            ${{ steps.figma.outputs.local_path }}

      - name: Update visual_baseline table
        run: |
          psql "${{ secrets.POSTGRES_URL }}" -c "
            INSERT INTO visual_baseline (route, viewport, baseline_url, figma_node_id, created_at)
            VALUES (
              '${{ steps.figma.outputs.route }}',
              '${{ steps.figma.outputs.viewport }}',
              'https://spdtwktxdalcfigzeqrz.supabase.co/storage/v1/object/public/baselines/${{ steps.figma.outputs.filename }}',
              '${{ github.event.client_payload.node_id }}',
              NOW()
            )
            ON CONFLICT (route, viewport)
            DO UPDATE SET baseline_url = EXCLUDED.baseline_url, updated_at = NOW();
          "

      - name: Run visual regression tests
        run: |
          node scripts/ssim-from-figma.js \
            --figma-node-id ${{ github.event.client_payload.node_id }} \
            --threshold-mobile 0.97 \
            --threshold-desktop 0.98
```

---

## Example Agent Conversation Flow

### Scenario: Designer updates BIR Status Dashboard

**1. Designer Action** (in Figma):
- Updates BIR Status Dashboard frame
- Changes status from "In Progress" → "Ready for dev"

**2. Webhook Received** (Vercel API route):
```typescript
// app/api/figma-webhook/route.ts
export async function POST(request: Request) {
  const payload = await request.json();

  if (payload.event_type === 'status_changed' && payload.new_status === 'ready_for_dev') {
    // Trigger GitHub Actions workflow
    await fetch('https://api.github.com/repos/Insightpulseai-net/archi-agent-framework/dispatches', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.GITHUB_TOKEN}`,
        'Accept': 'application/vnd.github.v3+json'
      },
      body: JSON.stringify({
        event_type: 'figma_status_changed',
        client_payload: payload
      })
    });
  }

  return Response.json({ status: 'ok' });
}
```

**3. Agent Execution** (GitHub Actions):
```bash
# Step 1: Export Figma frame as PNG (desktop 1920x1080)
figma_export_frame(
  file_id="ABC123XYZ",
  node_id="123:456",
  format="png",
  scale=2,
  viewport={width: 1920, height: 1080}
)
# → Downloads bir-status-desktop@2x.png

# Step 2: Upload to Supabase storage
supabase storage upload baselines/bir-status-desktop.png bir-status-desktop@2x.png

# Step 3: Update baseline table
INSERT INTO visual_baseline (route, viewport, baseline_url, figma_node_id)
VALUES ('/dashboard/bir-status', 'desktop', 'supabase://baselines/bir-status-desktop.png', '123:456');

# Step 4: Fetch Code Connect (if available)
figma_get_code_connect(
  file_id="ABC123XYZ",
  node_id="123:456",
  language="typescript"
)
# → Returns Code Connect snippet or auto-generated code

# Step 5: Generate Next.js page (if Code Connect available)
# Write to app/dashboard/bir-status/page.tsx

# Step 6: Commit changes
git add app/dashboard/bir-status/page.tsx
git commit -m "feat(dashboard): Update BIR Status Dashboard from Figma

Figma node: 123:456
Status: Ready for dev
Last edited: 2025-12-09T10:30:00Z

🤖 Generated with Claude Code (Figma Dev Mode-aware)
Co-Authored-By: Claude <noreply@anthropic.com>"

# Step 7: Create PR
gh pr create \
  --title "feat(dashboard): Update BIR Status Dashboard" \
  --body "Auto-generated from Figma Dev Mode\nNode ID: 123:456\nStatus: Ready for dev" \
  --base main

# Step 8: Run visual regression tests in PR CI
# (Compares deployed PR preview against Figma baseline)
```

**4. PR Visual Regression Check**:
```bash
# .github/workflows/pr-visual-regression.yml
- name: Visual regression test
  run: |
    # Deploy PR preview to Vercel
    PREVIEW_URL=$(vercel --yes | grep -o 'https://.*\.vercel\.app')

    # Capture screenshot from preview
    node scripts/snap.js --base-url="$PREVIEW_URL" --routes="/dashboard/bir-status" --output=pr-screenshot.png

    # Compare against Figma baseline
    node scripts/ssim.js \
      --baseline supabase://baselines/bir-status-desktop.png \
      --current pr-screenshot.png \
      --threshold 0.98

    # Fail PR if SSIM < 0.98
```

**5. PR Merged** → Vercel production deployment → Gate 7 ✅ PASS

---

## Expected Outcomes

### Immediate Benefits
1. **Visual Parity Gate Automation**: Gate 7 goes from manual → fully automated
2. **Design-Code Sync**: 100% fidelity between Figma and deployed UI
3. **Designer Autonomy**: Designers can trigger code generation without dev intervention
4. **Zero Visual Regressions**: SSIM thresholds enforced on every PR

### Medium-Term Benefits
1. **Design Token Single Source of Truth**: Figma variables → Supabase → Tailwind (bidirectional sync)
2. **Annotation-Driven Development**: Business logic, RLS policies, validation rules auto-generated from Figma
3. **Component Library Sync**: Figma components → React components with Code Connect
4. **Version History**: Track which Figma version corresponds to each deployment

### Long-Term Benefits
1. **Full Design-to-Production Pipeline**: Figma "Ready for dev" → deployed code in <5 minutes
2. **Design System Governance**: Enforce design system compliance via Figma variables
3. **Cross-Team Collaboration**: Designers, devs, QA all work from same source of truth
4. **Rollback Safety**: Revert to previous Figma version if deployment breaks

---

## Agent Behavior Rules

### DO
- ✅ Only parse frames marked "Ready for dev"
- ✅ Prefer Code Connect over auto-generated code
- ✅ Enforce SSIM thresholds (≥0.97 mobile, ≥0.98 desktop)
- ✅ Parse annotations for business logic
- ✅ Sync design tokens to Supabase and Tailwind
- ✅ Auto-generate RLS policies from annotations
- ✅ Commit generated code with Figma node IDs in commit message
- ✅ Block PRs that fail visual regression tests

### DON'T
- ❌ Parse frames not marked "Ready for dev"
- ❌ Use auto-generated code when Code Connect exists
- ❌ Deploy without running visual regression tests
- ❌ Ignore Figma annotations
- ❌ Hard-code colors/spacing (always use design tokens)
- ❌ Modify Figma files without designer approval
- ❌ Skip SSIM threshold checks

---

## Next Steps (Implementation Roadmap)

### Phase 1: MCP Server Setup (Week 1)
1. **Install Figma MCP Server** (port 3845)
2. **Configure Figma Personal Access Token**
3. **Test basic API calls** (figma_get_ready_frames, figma_export_frame)
4. **Set up webhook endpoint** (/api/figma-webhook)

### Phase 2: Visual Parity Automation (Week 2)
1. **Create visual_baseline table** in Supabase
2. **Implement baseline capture** from Figma Dev Mode
3. **Update scripts/ssim.js** to accept Figma node IDs
4. **Configure GitHub Actions** for auto-sync

### Phase 3: Code Generation (Week 3)
1. **Set up Code Connect** for design system components
2. **Generate Next.js pages** from Figma frames
3. **Extract design tokens** to Tailwind config
4. **Store tokens in Supabase** (theme_tokens table)

### Phase 4: Annotation-Driven Development (Week 4)
1. **Parse annotations** for RLS policies
2. **Generate validation rules** from annotations
3. **Auto-create state machines** from workflow annotations
4. **Document annotation conventions** for designers

### Phase 5: Full Automation (Week 5)
1. **End-to-end pipeline**: Figma "Ready for dev" → deployed code
2. **Bidirectional sync**: Code changes → update Figma
3. **Design system governance**: Enforce token usage
4. **Rollback safety**: Revert to previous Figma versions

---

## Success Criteria

**Gate 7 (Visual Parity) - Fully Automated**:
- [ ] All frames marked "Ready for dev" have baselines in Supabase
- [ ] SSIM ≥0.97 (mobile), ≥0.98 (desktop) enforced on all PRs
- [ ] Visual regression tests run automatically on every deployment
- [ ] Baselines auto-update when Figma status changes

**Code Generation**:
- [ ] 90%+ of dashboard code auto-generated from Figma
- [ ] Code Connect configured for all design system components
- [ ] Design tokens synchronized across Figma, Supabase, and Tailwind

**Annotation-Driven Development**:
- [ ] RLS policies auto-generated from annotations
- [ ] Validation rules auto-generated from annotations
- [ ] State machines auto-generated from workflow annotations

**Developer Experience**:
- [ ] Zero manual screenshot capture
- [ ] Zero manual design token updates
- [ ] Zero visual regressions in production
- [ ] Designer-triggered code generation (<5 min latency)

---

**Last Updated**: 2025-12-09
**Author**: Claude Code (Figma Dev Mode-Aware Agent)
**Status**: Master prompt ready for implementation
