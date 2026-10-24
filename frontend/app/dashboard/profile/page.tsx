"use client";

import { useState } from "react";
import { Icon } from "@/components/icon";
import { useWorkspace } from "@/components/workspace-provider";
import type { SupplierProfile } from "@/lib/types";

function ProfileForm({
  profile,
  onSave,
}: {
  profile: SupplierProfile;
  onSave: (profile: SupplierProfile) => void;
}) {
  const [draft, setDraft] = useState(profile);
  const [dirty, setDirty] = useState(false);
  function update(next: Partial<SupplierProfile>) {
    setDraft((previous) => ({ ...previous, ...next }));
    setDirty(true);
  }
  const numberValue = (value: string) =>
    value.trim() === "" ? null : Number(value);
  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        onSave(draft);
        setDirty(false);
      }}
      className="profile-form"
    >
      <div className="form-section">
        <div className="form-section-heading">
          <span>01</span>
          <div>
            <h2>The business behind the bid.</h2>
            <p>Your basic details and the categories you supply.</p>
          </div>
        </div>
        <div className="form-grid">
          <label>
            Business name
            <input
              required
              maxLength={100}
              value={draft.company}
              onChange={(event) => update({ company: event.target.value })}
            />
          </label>
          <label>
            Contact person
            <input
              required
              maxLength={100}
              value={draft.contact}
              onChange={(event) => update({ contact: event.target.value })}
            />
          </label>
          <label className="full-width">
            Email address
            <input
              type="email"
              required
              value={draft.email}
              onChange={(event) => update({ email: event.target.value })}
            />
          </label>
          <fieldset className="full-width category-fieldset">
            <legend>Supply categories</legend>
            <div>
              {["Lab equipment", "Electronics", "IT equipment"].map(
                (category) => (
                  <label
                    key={category}
                    className={`category-toggle ${draft.categories.includes(category) ? "is-active" : ""}`}
                  >
                    <input
                      type="checkbox"
                      checked={draft.categories.includes(category)}
                      onChange={(event) =>
                        update({
                          categories: event.target.checked
                            ? [...draft.categories, category]
                            : draft.categories.filter(
                                (value) => value !== category,
                              ),
                        })
                      }
                    />
                    <Icon name="check" size={14} />
                    {category}
                  </label>
                ),
              )}
            </div>
          </fieldset>
        </div>
      </div>
      <div className="form-section">
        <div className="form-section-heading">
          <span>02</span>
          <div>
            <h2>Your financial picture.</h2>
            <p>
              Enter exact annual amounts in INR. Leave an unknown value blank.
            </p>
          </div>
        </div>
        <div className="form-grid three-columns">
          {draft.turnover.map((entry, index) => (
            <label key={entry.year}>
              Turnover · FY {entry.year}
              <div className="input-prefix">
                <span>₹</span>
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={entry.amount ?? ""}
                  placeholder="Unknown"
                  onChange={(event) =>
                    update({
                      turnover: draft.turnover.map((item, position) =>
                        position === index
                          ? { ...item, amount: numberValue(event.target.value) }
                          : item,
                      ),
                    })
                  }
                />
              </div>
            </label>
          ))}
        </div>
        <div className="form-grid financial-extra">
          <label>
            Available deposit funds (INR)
            <div className="input-prefix">
              <span>₹</span>
              <input
                type="number"
                min="0"
                step="1"
                value={draft.depositCapacity ?? ""}
                placeholder="Unknown"
                onChange={(event) =>
                  update({ depositCapacity: numberValue(event.target.value) })
                }
              />
            </div>
            <small>
              Stated funding capacity; does not confirm EMD payment.
            </small>
          </label>
          <label>
            Completed relevant supply orders
            <input
              type="number"
              min="0"
              step="1"
              value={draft.completedOrders ?? ""}
              placeholder="Unknown"
              onChange={(event) =>
                update({ completedOrders: numberValue(event.target.value) })
              }
            />
            <small>
              Used for simple order-count checks in the sample workspace.
            </small>
          </label>
        </div>
      </div>
      <div className="form-section">
        <div className="form-section-heading">
          <span>03</span>
          <div>
            <h2>The details that open doors.</h2>
            <p>
              Record what you know. An unknown certificate always stays for
              review.
            </p>
          </div>
        </div>
        <div className="certificate-grid">
          {(
            [
              { key: "gst", label: "GST registration" },
              { key: "iso", label: "ISO 9001 certificate" },
              { key: "manufacturer", label: "Manufacturer authorization" },
            ] as const
          ).map((item) => (
            <label key={item.key}>
              <Icon name="shield" size={19} />
              <strong>{item.label}</strong>
              <select
                value={
                  draft.certificates[item.key] === null
                    ? "unknown"
                    : draft.certificates[item.key]
                      ? "present"
                      : "absent"
                }
                onChange={(event) =>
                  update({
                    certificates: {
                      ...draft.certificates,
                      [item.key]:
                        event.target.value === "unknown"
                          ? null
                          : event.target.value === "present",
                    },
                  })
                }
              >
                <option value="unknown">Unknown / not confirmed</option>
                <option value="present">Present</option>
                <option value="absent">Confirmed absent</option>
              </select>
            </label>
          ))}
        </div>
      </div>
      <div className="form-footer">
        <span>
          <Icon name="shield" size={16} />
          Stored in this browser. Use sample business facts.
        </span>
        <button
          type="submit"
          className="button button-dark button-small"
          disabled={!dirty}
        >
          <Icon name="check" size={16} />
          {dirty ? "Save profile" : "Profile up to date"}
        </button>
      </div>
    </form>
  );
}

export default function ProfilePage() {
  const { profile, saveProfile, ready } = useWorkspace();
  return (
    <>
      <div className="workspace-heading">
        <div>
          <div className="eyebrow">A STRONGER STARTING POINT</div>
          <h1>Your business, in focus.</h1>
          <p>
            A little detail today makes your next opportunity easier to assess.
          </p>
        </div>
        <span className="subtle-tag">
          <Icon name="building" size={14} />
          Supplier profile
        </span>
      </div>
      {ready ? (
        <ProfileForm profile={profile} onSave={saveProfile} />
      ) : (
        <div className="loading-panel">Loading your supplier profile…</div>
      )}
    </>
  );
}
