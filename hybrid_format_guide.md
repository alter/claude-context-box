# XML Hybrid Format Guide for CLAUDE.md

## Overview

This guide describes the XML Hybrid format used in CLAUDE.md - a balance between maximum clarity for LLM agents and token efficiency.

## Format Philosophy

### Core Principle
Use **XML for critical rules** where misinterpretation is costly, and **compact notation for simple lists** where context is clear.

### Why XML Works
- Claude is specifically trained to recognize XML tags with higher attention
- XML provides unambiguous structure separation
- Hierarchical nesting matches logical information flow
- Examples within XML eliminate pattern guessing

## Format Structure

### 1. Critical Sections (XML Required)

#### Stop Triggers
```xml
<critical_stops>
  <stop>
    <trigger>condition to watch for</trigger>
    <action>what to do instead</action>
    <example_wrong>bad pattern to avoid</example_wrong>
    <example_correct>good pattern to follow</example_correct>
  </stop>
</critical_stops>
```
**When to use**: Any rule where wrong interpretation causes significant damage.

#### Golden Rules
```xml
<golden_rules>
  <rule number="N">
    <name>short rule name</name>
    <rationale>why this matters</rationale>
    <validation>how to check compliance</validation>
  </rule>
</golden_rules>
```
**When to use**: Core principles that govern all behavior.

#### Procedures with Checkpoints
```xml
<mandatory_procedure>
  <step number="N">
    <action>what to do</action>
    <purpose>why doing it</purpose>
    <checkpoint>validation before next step</checkpoint>
  </step>
</mandatory_procedure>
```
**When to use**: Multi-step processes where order matters.

### 2. Diagnostic/Testing Sections (XML with Expected)

```xml
<diagnosis_protocol>
  <quick_check>
    <command>exact command to run</command>
    <checks_for>what we're looking for</checks_for>
    <expected>expected output/state</expected>
  </quick_check>
</diagnosis_protocol>
```
**When to use**: Any check where agent needs to validate output.

### 3. Compact Sections (Simple Format)

#### Lists and Mappings
```markdown
## SHORTCUTS
u → .claude/update.py
c → .claude/check.py
```
**When to use**: Simple 1:1 mappings with no ambiguity.

#### Permissions and Restrictions
```markdown
## PERMISSIONS
WITHOUT: modify,delete,create
WITH: read,test,search
```
**When to use**: Clear binary choices (allowed/forbidden).

### 4. File Structure Definitions (XML for Clarity)

```xml
<context_files>
  <file name="CONTEXT.llm">
    <location>where it goes</location>
    <never_create_in>forbidden locations</never_create_in>
    <structure>
      YAML or JSON structure example
    </structure>
  </file>
</context_files>
```
**When to use**: File specifications needing precise structure.

## Token Optimization Strategies

### Strategy 1: Graduated Detail
- **Critical stops**: Full XML with examples (15-20 tokens each)
- **Rules**: XML with validation (10-15 tokens each)
- **Lists**: Compact format (2-3 tokens each)

### Strategy 2: Example Placement
- Place examples only where patterns aren't obvious
- Use wrong/correct pairs for complex concepts
- Skip examples for simple commands (chmod, curl)

### Strategy 3: Grouping
- Group related items under single XML parent
- Use consistent attribute names (number, name, action)
- Avoid deep nesting beyond 3 levels

## Metrics and ROI

### Token Usage (4000-4500 total)
- Critical stops: ~800 tokens (20%)
- Golden rules: ~600 tokens (15%)
- Procedures: ~500 tokens (12%)
- Diagnosis: ~400 tokens (10%)
- Context files: ~700 tokens (17%)
- Compact sections: ~1000 tokens (25%)

### Error Reduction
- XML sections: <5% interpretation errors
- Compact sections: <15% interpretation errors
- Overall: <10% vs 30%+ with pure compact format

### Time Savings
- -80% debugging time from clear examples
- -60% back-and-forth clarifications
- +200% initial understanding speed

## Maintenance Guidelines

### When to Add XML
- New critical rule that could be misinterpreted
- Procedure with multiple validation points
- Any rule causing repeated agent failures

### When to Keep Compact
- Simple mappings (shortcuts, aliases)
- Binary choices (yes/no, allowed/forbidden)
- Well-established conventions (file extensions)

### Version Control
- Keep XML structure stable (tags, attributes)
- Update examples when patterns change
- Add new stops/rules as discovered
- Review quarterly for redundancy

## Template for New Rules

### Critical Rule Template
```xml
<stop>
  <trigger>specific condition</trigger>
  <action>exact action to take</action>
  <example_wrong>concrete bad example</example_wrong>
  <example_correct>concrete good example</example_correct>
  <rationale>why this matters (optional)</rationale>
</stop>
```

### Diagnostic Check Template
```xml
<quick_check>
  <command>command to run</command>
  <checks_for>what we're validating</checks_for>
  <expected>expected result</expected>
  <if_not>action if check fails</if_not>
</quick_check>
```

## Integration with Projects

### Project-Specific Adaptations
1. Keep XML structure for universal rules
2. Update examples to match project patterns
3. Add project-specific stops in same XML format
4. Maintain compact format for project shortcuts

### Multi-Project Usage
- Core CLAUDE.md with universal rules (XML)
- PROJECT.llm with project specifics (YAML/XML mix)
- CONTEXT.llm per module (YAML preferred)

## Validation Process

### Pre-deployment Checklist
- [ ] All stops have wrong/correct examples
- [ ] All procedures have checkpoints
- [ ] File locations are explicit
- [ ] No ambiguous compact notation for critical rules
- [ ] Total size under 5000 tokens

### Testing Protocol
1. Test each stop trigger with real scenario
2. Verify examples match current codebase
3. Check XML parsing (no broken tags)
4. Validate checkpoint sequences
5. Confirm file structure specs are complete

## Common Pitfalls to Avoid

### Over-XML-ification
Don't wrap everything in XML. Simple lists work fine compact.

### Under-Exampling
Critical rules need examples. Don't skip to save tokens.

### Inconsistent Structure
Keep XML patterns consistent. Same attributes, same nesting.

### Missing Validations
Every rule needs a way to check compliance.

## Evolution Strategy

### Continuous Improvement
- Track agent failures → add stops
- Monitor misinterpretations → add examples
- Review token usage → optimize grouping
- Gather feedback → adjust format

### Deprecation Process
- Mark obsolete rules with deprecated="true"
- Keep for 1 version cycle
- Remove after verification
- Document removal reason

## Success Metrics

### Measure Monthly
- Agent error rate (target: <10%)
- Time to task completion
- Clarification requests (fewer = better)
- Token usage efficiency
- Rule compliance rate

### Optimization Triggers
- Error rate >15% → Add more examples
- Token usage >5000 → Consolidate compact sections
- Clarifications >3/task → Improve XML clarity
- Compliance <90% → Add validation checks

## Conclusion

The XML Hybrid format provides optimal balance:
- **Maximum clarity** where it matters (critical rules)
- **Token efficiency** where possible (simple lists)
- **Self-validation** through examples and checkpoints
- **Maintainability** through consistent structure

This format should evolve with usage but maintain core XML structure for critical sections.