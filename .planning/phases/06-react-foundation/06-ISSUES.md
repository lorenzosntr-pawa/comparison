# UAT Issues: Phase 6 React Foundation

**Tested:** 2026-01-20
**Source:** .planning/phases/06-react-foundation/06-01-SUMMARY.md through 06-04-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

None.

## Resolved Issues

### UAT-001: Sidebar overlays main content when collapsed
**Resolved:** 2026-01-20 - Fixed via CSS override
**Fix:** Added CSS rules in index.css to force sidebar spacer width transitions based on data-collapsible and data-state attributes. The shadcn sidebar Tailwind v4 classes weren't applying correctly.

### UAT-002: Vite API proxy not rewriting /api prefix
**Resolved:** 2026-01-20 - Fixed during UAT
**Fix:** Added `rewrite: (path) => path.replace(/^\/api/, '')` to vite.config.ts proxy configuration.

### UAT-003: Dev server default port (5173) not accessible
**Resolved:** 2026-01-20 - Fixed during UAT
**Fix:** Changed vite.config.ts to use `host: '0.0.0.0'` and `port: 3000`. Environment-specific issue, possibly related to VPN/network configuration.

---

*Phase: 06-react-foundation*
*Tested: 2026-01-20*
