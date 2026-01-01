# Evaluation Checklist for docs2code Skill

## Accuracy

- [ ] Generated code compiles/runs correctly
- [ ] All fields from specification are present
- [ ] All actions from specification are implemented
- [ ] Computed fields have correct formulas
- [ ] Field types match specification exactly
- [ ] Required flags match specification

## Completeness

- [ ] All required files are generated
- [ ] __manifest__.py has correct dependencies
- [ ] Security rules are defined
- [ ] Views are functional
- [ ] Tests cover main functionality
- [ ] Regeneration headers present in all files

## Scope Discipline

- [ ] No features beyond specification
- [ ] No extra fields added
- [ ] No additional endpoints
- [ ] Dependencies are minimal
- [ ] Follows Smart Delta priority (CE > OCA > Custom)

## Code Quality

- [ ] Follows Odoo 18 CE conventions
- [ ] Proper Python formatting (PEP 8)
- [ ] XML is valid and formatted
- [ ] No hardcoded values
- [ ] Proper error handling

## Security

- [ ] No SQL injection vectors
- [ ] No hardcoded credentials
- [ ] Access rights properly configured
- [ ] Sensitive fields use appropriate widgets
- [ ] RLS policies where needed

## Testing

- [ ] Test stubs included for all models
- [ ] Edge cases identified in tests
- [ ] Fixtures use realistic data
- [ ] Tests are tagged correctly
- [ ] Test class inherits TransactionCase

## Documentation

- [ ] Source document is referenced
- [ ] Generation timestamp is included
- [ ] DO NOT EDIT warning present
- [ ] Module description is accurate

---

## Scoring

| Category | Weight | Score (0-10) |
|----------|--------|--------------|
| Accuracy | 25% | |
| Completeness | 20% | |
| Scope Discipline | 15% | |
| Code Quality | 15% | |
| Security | 15% | |
| Testing | 5% | |
| Documentation | 5% | |
| **Total** | 100% | |

### Pass Criteria
- Individual category: Minimum 7/10
- Overall weighted: Minimum 8/10

---

*Evaluation version: 1.0.0*
*Last updated: 2025-12-31*
