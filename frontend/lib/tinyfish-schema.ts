export const DISCOVERY_SCHEMA = {
  type: "object",
  properties: {
    outcome: { type: "string", enum: ["success", "no_matches", "failed"] },
    failure_reason: { type: "string", nullable: true },
    notices: {
      type: "array",
      maxItems: 5,
      items: {
        type: "object",
        properties: {
          notice_id: { type: "string", nullable: true },
          title: { type: "string" },
          source_url: { type: "string" },
          deadline_text: { type: "string", nullable: true },
          pdf_urls: { type: "array", items: { type: "string" } },
          amendment_urls: { type: "array", items: { type: "string" } },
        },
        required: [
          "notice_id",
          "title",
          "source_url",
          "deadline_text",
          "pdf_urls",
          "amendment_urls",
        ],
      },
    },
  },
  required: ["outcome", "failure_reason", "notices"],
};
