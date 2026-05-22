# Troubleshooting Phase: TDD-Guided Problem Diagnosis

**Purpose:** Apply TDD discipline to debugging and problem diagnosis
**When to use:** When investigating production issues, test failures, or unexpected behavior
**Prerequisites:** Clear problem description or failing scenario
**Expected output:** Root cause identification with test coverage or diagnostic logging
**Typical duration:** 30 minutes to 2+ hours depending on complexity
**Next step:** Return to normal TDD flow (2) for fixes, or completeness check (3)
**Critical:** Maintain TDD discipline even in diagnostic mode

---
```markdown

## **TDD + Production Debugging - Step [X]**
We're implementing: [specific diagnostic/fix step]

## **🚨 TDD CHECK (Troubleshooting Mode) 🚨**
- [ ] **RED**: Failing test OR diagnostic logging added first
- [ ] **GREEN**: Test passes OR hypothesis confirmed via logs  
- [ ] **Simple**: One focused change at a time

## **RED Phase Options:**
1. Write failing test (traditional)
2. Add targeted logging (diagnostic)
3. Enhanced production logging (analysis)

## **Production-Safe Logging:**
- INFO level+, human-readable, no sensitive data
- Log key decision points & data state transitions
- Safe to leave in production

## **Ready for commit?** 
- [ ] Test failing OR logging added ✅
- [ ] Passes OR hypothesis confirmed ✅  
- [ ] Code clean ✅
- [ ] Root cause identified (for fixes) ✅

**Next:** What's the next smallest testable/diagnosable piece?
**⚠️ Alert:** User intervenes if TDD discipline breaks OR debugging becomes unfocused!

```


---

## License & Attribution

This template is part of the Human-AI TDD Collaboration Process framework.

**License:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)

**Attribution:** Process framework developed by [Ken Judy](https://github.com/kenjudy) with Claude Anthropic 4

**Usage:** You are free to use, modify, and distribute this template with appropriate attribution. 

**Source:** [PDCA Framework Repository](https://github.com/kenjudy/pdca-framework)

---
*2025*