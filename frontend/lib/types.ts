// BUILD_SPEC §3 names `lib/types.ts` as the home for API response types; §2's
// tree gives the frontend a `types/` directory. The definitions live in
// `types/api.ts` and are re-exported here so both references resolve and there
// is still only one definition of each type.
export * from "@/types/api";
