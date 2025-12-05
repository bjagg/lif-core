export default {
  rules: {
    "scope-empty": [2, "never"],
    "scope-case": [0],
    "scope-min-length": [2, "always", 4],
    "subject-empty": [2, "never"],
    "subject-min-length": [2, "always", 4],
    "header-max-length": [0, "always", 72],
    "body-leading-blank": [2, "always"],
  },
  parserPreset: {
    parserOpts: {
      headerPattern: /^((Issue #)\d+(?:, (Issue #)\d+)*):\s(.*)$/,
      headerCorrespondence: ["scope", "subject"],
    },
  },
};
