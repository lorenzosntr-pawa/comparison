# UAT Issues: Phase 35 Plan 01

**Tested:** 2026-01-28
**Source:** .planning/phases/35-remediation/35-01-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Investigation Results

**Phase 35 fixes verified working:**
- DISTINCT SR ID counting: PASS (252 -> 131 reduction confirmed)
- Match rate accuracy: PASS (~83-84% showing correctly)
- Event matching logic: PASS (SQL query confirmed all linkable events are linked)

**Root cause identified:** The issues reported are NOT matching/linking bugs but **tournament discovery gaps** - competitor events exist on websites but were never scraped into the database.

## Open Issues

### UAT-001: Competitor tournament discovery incomplete

**Discovered:** 2026-01-28
**Phase/Plan:** 35-01
**Severity:** Major (downgraded from Blocker)
**Feature:** Competitor event scraping / Tournament discovery
**Description:** Events from certain leagues are available on competitor websites but do not exist in the competitor_events table. The matching system works correctly - it just doesn't have competitor data to match against.

**Investigation Evidence:**
- SQL Query: All "BetPawa-only" events show NO in both on_sportybet and on_bet9ja columns
- This means competitor_events table has no entries for these SR IDs
- User verified events ARE available on competitor websites
- Conclusion: Tournament discovery is missing these leagues on competitor platforms

**Complete List of Missing Tournaments (from SQL Query 4):**

| Tournament | Country | BetPawa Events | Competitor Events |
|------------|---------|----------------|-------------------|
| FA Trophy | England | 8 | 0 |
| 2nd Division | Egypt | 8 | 0 |
| Coppa Italia, Women | Italy | 4 | 0 |
| FA Trophy | Malta | 3 | 0 |
| Arabian Gulf League | United Arab Emirates | 3 | 0 |
| KNVB beker, Women | Netherlands | 3 | 0 |
| ASEAN Club Championship | International | 3 | 0 |
| U23 Pro League | United Arab Emirates | 3 | 0 |
| League Cup A | Iceland | 2 | 0 |
| League Cup | Northern Ireland | 2 | 0 |
| Sultan Cup | Oman | 2 | 0 |
| FIFA Champions Cup, Women | International | 1 | 0 |
| FIFA World Cup Qualification, Inter-Confederation Playoffs | International | 1 | 0 |
| U21 Elite League | Saudi Arabia | 1 | 0 |
| Supercopa Uruguaya | Uruguay | 1 | 0 |
| Coppa Italia Serie C | Italy | 1 | 0 |
| Super Cup | Kuwait | 1 | 0 |
| Primera Division | Venezuela | 1 | 0 |
| National League | Myanmar | 1 | 0 |
| Copa Chile | Chile | 1 | 0 |

**Total: 20 tournaments, ~57 events missing competitor coverage**

**Sample Events Verified (Query 5C - all showing NO/NO for competitors):**
```
2nd Division     62384002  Maleyat Kafr El Zayat - La Viena FC      NO  NO
2nd Division     62383996  El Entag El Harby - Tanta FC             NO  NO
2nd Division     62384004  El Dakhleya Sc - El Terasanah            NO  NO
Arabian Gulf     67315424  Al Wasl FC - Khor Fakkan Club            NO  NO
Arabian Gulf     67315426  AL Bataeh (UAE) - Al Jazira (UAE)        NO  NO
Coppa Italia W   67203038  AS Roma Women - Lazio Rome Women         NO  NO
FA Trophy        67602192  Floriana FC - Zabbar Saint Patrick FC   NO  NO
FA Trophy        67820196  Chatham Town - Southend United           NO  NO
```

**Expected:** Competitor scraper should discover and scrape these tournaments
**Actual:** Tournaments not discovered, events never scraped

**Root Cause Options:**
1. Tournaments exist under different navigation hierarchy on competitors
2. Tournament discovery hasn't been run recently
3. Discovery doesn't reach these tournament categories (cups, women's leagues, lower divisions)

**NOT a matching bug:** SQL confirmed: zero competitor events have matching SR IDs but NULL betpawa_event_id

**Recommendation:** Future phase should investigate competitor tournament discovery to expand coverage for:
- Cup competitions (FA Trophy, Copa Chile, Sultan Cup, etc.)
- Women's leagues (Coppa Italia Women, KNVB beker Women, FIFA Champions Cup Women)
- Lower divisions (Egypt 2nd Division)
- Regional leagues (Arabian Gulf, Myanmar National League, Venezuela Primera)

## Resolved Issues

### UAT-002: Events in same tournaments not matched (DUPLICATE)

**Original report:** Events not matched despite existing on competitors
**Resolution:** 2026-01-28 - Merged into UAT-001 after investigation confirmed root cause. Events aren't "unmatched" - they're "never scraped". The matching logic works perfectly; competitor events simply don't exist in the database.

---

*Phase: 35-remediation*
*Plan: 01*
*Tested: 2026-01-28*
