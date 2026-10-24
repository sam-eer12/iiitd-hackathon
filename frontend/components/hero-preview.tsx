"use client";

import {
  animate,
  motion,
  useInView,
  useMotionValue,
  usePageInView,
  useReducedMotion,
  useSpring,
  useTransform,
  type MotionValue,
} from "motion/react";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  useSyncExternalStore,
} from "react";
import { Icon } from "./icon";
import { INITIAL_TENDER_CATALOG } from "@/lib/tender-catalog";

/* Orbit path (px, relative to the document's center). The document is
   420 x 482 with its text inset 24px at the sides and 20px at the bottom;
   side cards are about 254 x 130. The path keeps every card clear of the
   document's text at all times:
   - Behind (top half): a shallow arc the document fully hides.
   - In front (bottom half): down the side, around a rounded corner and
     beneath the document, never across it. */
const SIDE_X = 345;
const BACK_Y = 60;
const FRONT_Y = 334;
const CORNER = 110;

/* Front route from the right rest point to the left one, sampled once and
   walked by distance so the speed stays even around the corners. */
const FRONT_ROUTE = (() => {
  const points: [number, number][] = [];
  const inner = SIDE_X - CORNER;
  const steps = 24;
  for (let i = 0; i <= steps; i++)
    points.push([SIDE_X, ((FRONT_Y - CORNER) * i) / steps]);
  for (let i = 1; i <= steps; i++) {
    const a = ((Math.PI / 2) * i) / steps;
    points.push([
      inner + CORNER * Math.cos(a),
      FRONT_Y - CORNER + CORNER * Math.sin(a),
    ]);
  }
  for (let i = 1; i <= steps; i++)
    points.push([inner - (2 * inner * i) / steps, FRONT_Y]);
  for (let i = 1; i <= steps; i++) {
    const a = Math.PI / 2 + ((Math.PI / 2) * i) / steps;
    points.push([
      -inner + CORNER * Math.cos(a),
      FRONT_Y - CORNER + CORNER * Math.sin(a),
    ]);
  }
  for (let i = 1; i <= steps; i++)
    points.push([-SIDE_X, FRONT_Y - CORNER - ((FRONT_Y - CORNER) * i) / steps]);
  const lengths = [0];
  for (let i = 1; i < points.length; i++)
    lengths.push(
      lengths[i - 1] +
        Math.hypot(
          points[i][0] - points[i - 1][0],
          points[i][1] - points[i - 1][1],
        ),
    );
  return { points, lengths, total: lengths[lengths.length - 1] };
})();

/* Position on the loop for an angle in radians: 0 = right rest point,
   pi = left rest point; 0..pi is the front route, pi..2pi the back arc. */
function orbitPoint(t: number): [number, number] {
  const turn = ((t % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI);
  if (turn > Math.PI) return [SIDE_X * Math.cos(turn), BACK_Y * Math.sin(turn)];
  const { points, lengths, total } = FRONT_ROUTE;
  const target = (turn / Math.PI) * total;
  let i = 1;
  while (i < lengths.length - 1 && lengths[i] < target) i++;
  const span = lengths[i] - lengths[i - 1] || 1;
  const k = (target - lengths[i - 1]) / span;
  return [
    points[i - 1][0] + (points[i][0] - points[i - 1][0]) * k,
    points[i - 1][1] + (points[i][1] - points[i - 1][1]) * k,
  ];
}

/* The guide line drawn behind the cards, from the same path. */
const ORBIT_PATH = (() => {
  const segments: string[] = [];
  for (let i = 0; i <= 120; i++) {
    const [x, y] = orbitPoint((2 * Math.PI * i) / 120);
    segments.push(`${i ? "L" : "M"}${x.toFixed(1)} ${y.toFixed(1)}`);
  }
  return `${segments.join(" ")} Z`;
})();

/* Rest-and-sweep rhythm: the cards rest beside the document, then make one
   smooth half-turn (one passing beneath, the other behind) and rest again. */
const REST_SECONDS = 4.4;
const SWEEP_SECONDS = 2.8;
const TURN_SECONDS = 2 * (REST_SECONDS + SWEEP_SECONDS);
const SWEEP_EASE = [0.65, 0, 0.35, 1] as const;

/* The orbit runs only where the cards fit beside the document. Narrower
   screens use the still tablet and phone layouts in hero-preview.css. */
const WIDE_QUERY = "(min-width: 981px)";
function subscribeToWidth(onChange: () => void) {
  const query = window.matchMedia(WIDE_QUERY);
  query.addEventListener("change", onChange);
  return () => query.removeEventListener("change", onChange);
}
const isWide = () => window.matchMedia(WIDE_QUERY).matches;
const isWideOnServer = () => false;

function OrbitCard({
  angle,
  pop,
  phase,
  side,
  children,
}: {
  angle: MotionValue<number>;
  pop: MotionValue<number>;
  phase: number;
  side: "left" | "right";
  children: React.ReactNode;
}) {
  // All values derive from two motion values, so the orbit never re-renders.
  // depth = sin(theta): 1 in front of the document, -1 behind it.
  const theta = useTransform(angle, (a) => ((a + phase) * Math.PI) / 180);
  const point = useTransform([theta, pop], ([t, p]: number[]) => {
    const [px, py] = orbitPoint(t);
    return { x: px * p, y: py * p };
  });
  const x = useTransform(point, (value) => value.x);
  const y = useTransform(point, (value) => value.y);
  const scale = useTransform(
    [theta, pop],
    ([t, p]: number[]) => (0.6 + 0.4 * p) * (0.92 + 0.08 * Math.sin(t)),
  );
  // Each card turns slightly toward the center as if following the ring.
  const rotateY = useTransform(
    [theta, pop],
    ([t, p]: number[]) => -Math.cos(t) * 12 * p,
  );
  const opacity = useTransform([theta, pop], ([t, p]: number[]) => {
    const depth = Math.sin(t);
    return Math.min(1, p * 1.6) * (depth < 0 ? 1 + 0.5 * depth : 1);
  });
  // A soft focus pull while emerging; no filter once settled.
  const filter = useTransform(pop, (p) =>
    p > 0.98 ? "none" : `blur(${((1 - p) * 8).toFixed(2)}px)`,
  );
  const zIndex = useTransform(theta, (t) => (Math.sin(t) > 1e-6 ? 3 : 0));
  return (
    <motion.div
      className={`orbit-anchor orbit-${side}`}
      style={{
        x,
        y,
        scale,
        rotateY,
        opacity,
        filter,
        zIndex,
        transformPerspective: 900,
      }}
    >
      {children}
    </motion.div>
  );
}

export function HeroPreview() {
  const tender = INITIAL_TENDER_CATALOG.tenders[0];
  const wide = useSyncExternalStore(subscribeToWidth, isWide, isWideOnServer);
  const reduceMotion = useReducedMotion();
  const orbiting = wide && !reduceMotion;

  const stage = useRef<HTMLElement>(null);
  const inView = useInView(stage, { amount: 0.25 });
  const pageVisible = usePageInView();
  const [userPaused, setUserPaused] = useState(false);

  const angle = useMotionValue(0);
  const popRight = useMotionValue(0);
  const popLeft = useMotionValue(0);
  // Pointer tilt for the center card, smoothed by springs (no re-renders).
  const tiltX = useSpring(0, { stiffness: 140, damping: 22 });
  const tiltY = useSpring(0, { stiffness: 140, damping: 22 });

  const rotation = useRef<ReturnType<typeof animate> | null>(null);
  const hovered = useRef(false);
  const shouldRun = useRef({ inView: false, pageVisible: true, paused: false });

  const syncPlayback = useCallback(() => {
    const spin = rotation.current;
    if (!spin) return;
    const { inView, pageVisible, paused } = shouldRun.current;
    if (paused || hovered.current || !inView || !pageVisible) spin.pause();
    else spin.play();
  }, []);

  // Pop the cards out from behind the document, then start the orbit.
  useEffect(() => {
    if (!orbiting) return;
    angle.set(0);
    popRight.set(0);
    popLeft.set(0);
    const settle = {
      type: "spring",
      visualDuration: 0.95,
      bounce: 0.16,
    } as const;
    const right = animate(popRight, 1, { ...settle, delay: 0.85 });
    const left = animate(popLeft, 1, { ...settle, delay: 1 });
    // The first rest segment also gives the cards time to settle.
    const spin = animate(angle, [0, 0, 180, 180, 360], {
      duration: TURN_SECONDS,
      times: [
        0,
        REST_SECONDS / TURN_SECONDS,
        (REST_SECONDS + SWEEP_SECONDS) / TURN_SECONDS,
        (2 * REST_SECONDS + SWEEP_SECONDS) / TURN_SECONDS,
        1,
      ],
      ease: ["linear", SWEEP_EASE, "linear", SWEEP_EASE],
      repeat: Infinity,
    });
    rotation.current = spin;
    syncPlayback();
    return () => {
      right.stop();
      left.stop();
      spin.stop();
      rotation.current = null;
    };
  }, [orbiting, angle, popRight, popLeft, syncPlayback]);

  // Pause off screen, in a hidden tab, or when the visitor asks.
  useEffect(() => {
    shouldRun.current = { inView, pageVisible, paused: userPaused };
    syncPlayback();
  }, [inView, pageVisible, userPaused, syncPlayback]);

  const amendment = (
    <div className="preview-amendment">
      <span className="amendment-icon">
        <Icon name="history" size={18} />
      </span>
      <div>
        <strong>The source. Within reach.</strong>
        <p>Read the original tender document</p>
        <span>
          <a href={tender.pdfUrls[0]} target="_blank" rel="noreferrer">
            Open source PDF <Icon name="arrow" size={12} />
          </a>
        </span>
      </div>
    </div>
  );
  const readiness = (
    <div className="preview-readiness">
      <span className="readiness-check">
        <Icon name="clock" size={18} />
      </span>
      <div>
        <strong>Ready for your review.</strong>
        <small>PDF clause verification pending</small>
      </div>
    </div>
  );

  return (
    <figure
      ref={stage}
      className={`hero-product reveal reveal-5 ${orbiting ? "is-orbiting" : ""}`}
      aria-label="Real IIIT-Delhi tender collected by TinyFish"
      onPointerEnter={(event) => {
        if (event.pointerType !== "mouse") return;
        hovered.current = true;
        syncPlayback();
      }}
      onPointerMove={(event) => {
        if (!orbiting || event.pointerType !== "mouse" || !stage.current)
          return;
        const box = stage.current.getBoundingClientRect();
        const px = ((event.clientX - box.left) / box.width) * 2 - 1;
        const py = ((event.clientY - box.top) / box.height) * 2 - 1;
        tiltY.set(px * 5);
        tiltX.set(-py * 4);
      }}
      onPointerLeave={() => {
        hovered.current = false;
        tiltX.set(0);
        tiltY.set(0);
        syncPlayback();
      }}
    >
      <div className="preview-glow" aria-hidden="true" />
      <div className="preview-stage">
        <svg
          className="orbit-ring"
          viewBox="-480 -120 960 560"
          aria-hidden="true"
          focusable="false"
        >
          <path d={ORBIT_PATH} />
        </svg>
        <motion.div
          className="preview-document"
          style={{
            rotateX: tiltX,
            rotateY: tiltY,
            transformPerspective: 1200,
          }}
        >
          <div className="document-topline">
            <span className="mini-document">
              <Icon name="document" size={17} />
            </span>
            <span>YOUR NEXT OPPORTUNITY</span>
            <Icon name="bookmark" size={16} />
          </div>
          <div className="preview-issuer">
            <span className="institution-symbol">II</span> INSTITUTIONAL
            PROCUREMENT
          </div>
          <h3>{tender.title}</h3>
          <div className="preview-tags">
            <span>IIIT-Delhi</span>
            <span>Official notice</span>
          </div>
          <div className="preview-facts">
            <div>
              <small>Estimated value</small>
              <strong>{tender.value}</strong>
            </div>
            <div>
              <small>Closing date</small>
              <strong>{tender.deadlineText}</strong>
            </div>
          </div>
          <div className="preview-condition">
            <Icon name="clock" size={16} />
            <span>Turnover requirement</span>
            <b>Review</b>
          </div>
          <div className="preview-condition">
            <Icon name="clock" size={16} />
            <span>Past experience</span>
            <b>Review</b>
          </div>
          <div className="preview-condition">
            <Icon name="clock" size={16} />
            <span>Required certificates</span>
            <b>Review</b>
          </div>
          <div className="preview-source">
            <Icon name="link" size={13} /> Official tender PDF linked.
          </div>
        </motion.div>
        {orbiting ? (
          <>
            <OrbitCard angle={angle} pop={popLeft} phase={180} side="left">
              {readiness}
            </OrbitCard>
            <OrbitCard angle={angle} pop={popRight} phase={0} side="right">
              {amendment}
            </OrbitCard>
          </>
        ) : (
          <>
            <div className="orbit-anchor orbit-left">{readiness}</div>
            <div className="orbit-anchor orbit-right">{amendment}</div>
          </>
        )}
      </div>
      <figcaption className="preview-sample">
        Real notice · TinyFish source snapshot
        {orbiting && (
          <button
            type="button"
            className="preview-motion-toggle"
            aria-pressed={userPaused}
            onClick={() => setUserPaused(!userPaused)}
          >
            <Icon name={userPaused ? "play" : "pause"} size={12} />
            {userPaused ? "Play motion" : "Pause motion"}
          </button>
        )}
      </figcaption>
    </figure>
  );
}
