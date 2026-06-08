import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

type ProjectKind = "matcha" | "mobile" | "transfer" | "dashboard";

type Project = {
  title: string;
  meta: string;
  kind: ProjectKind;
};

const projects: Project[] = [
  { title: "Droppable", meta: "DESKTOP APP * 2023", kind: "transfer" },
  { title: "Wunderflats App", meta: "MOBILE * 2024", kind: "mobile" },
  { title: "Landlord OS", meta: "DASHBOARD * 2026", kind: "dashboard" },
  { title: "SummerRain", meta: "DTC BRAND * 2022", kind: "matcha" },
];

const clamp = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};

const wrappedDistance = (index: number, center: number, total: number) => {
  let diff = index - (center % total);
  if (diff > total / 2) diff -= total;
  if (diff < -total / 2) diff += total;
  return diff;
};

const slotValue = (slot: number, values: [number, number, number, number, number]) =>
  interpolate(slot, [-2, -1, 0, 1, 2], values, {
    ...clamp,
    easing: Easing.bezier(0.65, 0, 0.35, 1),
  });

export const LuxuryPerspectiveGalleryHeroDepth: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const holdFrames = fps * 1.25;
  const moveFrames = fps * 1.2;
  const cycleFrames = holdFrames + moveFrames;
  const cycle = Math.floor(frame / cycleFrames);
  const cycleFrame = frame % cycleFrames;
  const springProgress =
    cycleFrame < holdFrames
      ? 0
      : spring({
          frame: cycleFrame - holdFrames,
          fps,
          config: {
            damping: 27,
            stiffness: 74,
            mass: 1.35,
          },
        });
  const active = cycle + interpolate(springProgress, [0, 1], [0, 1], clamp);

  return (
    <AbsoluteFill className="overflow-hidden bg-[#080B11] text-white">
      <StarField />
      <DepthFloor />
      <RomanHeader />
      <PointerGlyph frame={frame} />

      <main
        className="absolute inset-0"
        style={{
          perspective: 1900,
          transformStyle: "preserve-3d",
        }}
      >
        {projects.map((project, index) => {
          const slot = wrappedDistance(index, active, projects.length);
          const normalizedSlot = Math.max(-2, Math.min(2, slot));
          const abs = Math.abs(normalizedSlot);
          const isHero = abs < 0.5;
          const width = slotValue(normalizedSlot, [190, 290, 690, 230, 120]);
          const height = slotValue(normalizedSlot, [260, 360, 830, 300, 170]);
          const x = slotValue(normalizedSlot, [330, 690, 1710, 1082, 910]);
          const y = slotValue(normalizedSlot, [680, 610, 665, 600, 585]);
          const z = slotValue(normalizedSlot, [-680, -280, 260, -480, -900]);
          const rotateY = slotValue(normalizedSlot, [28, 12, -5, -10, -18]);
          const rotateX = slotValue(normalizedSlot, [1, 0, 0, 0, 1]);
          const opacity = slotValue(normalizedSlot, [0, 0.9, 1, 0.5, 0]);
          const blur = slotValue(normalizedSlot, [7, 0, 0, 5, 9]);
          const scale = slotValue(normalizedSlot, [0.7, 1, 1, 0.82, 0.55]);

          return (
            <DepthCard
              key={project.title}
              project={project}
              isHero={isHero}
              style={{
                width,
                height,
                opacity,
                zIndex: Math.round(1000 - Math.abs(normalizedSlot) * 120 + z / 20),
                filter: `blur(${blur}px)`,
                transform: [
                  "translate(-50%, -50%)",
                  `translate3d(${x - 960}px, ${y - 540}px, ${z}px)`,
                  `rotateX(${rotateX}deg)`,
                  `rotateY(${rotateY}deg)`,
                  `scale(${scale})`,
                ].join(" "),
              }}
            />
          );
        })}
      </main>

      <button className="absolute bottom-[34px] left-1/2 z-[1200] h-[72px] w-[252px] -translate-x-1/2 rounded-[22px] border border-white/[0.55] bg-[linear-gradient(180deg,#f3f7ff_0%,#c4cce0_100%)] text-[18px] font-black tracking-[0.12em] text-[#171d2a] shadow-[0_0_34px_rgba(159,178,255,0.35),inset_0_1px_0_rgba(255,255,255,0.9)]">
        SAY HELLO
      </button>
    </AbsoluteFill>
  );
};

const RomanHeader: React.FC = () => (
  <header className="absolute left-0 right-0 top-[46px] z-[1200] flex justify-center">
    <div className="flex items-center gap-4 text-[25px] font-black tracking-[-0.02em] text-white">
      <div className="grid h-[66px] w-[66px] place-items-center rounded-[22px] border border-white/[0.20] bg-[#eff3fb] text-[38px] shadow-[0_0_32px_rgba(208,222,255,0.22)]">
        🧑
      </div>
      <span>Roman</span>
      <span className="text-[30px] leading-none text-white/[0.88]">≡</span>
    </div>
  </header>
);

const StarField: React.FC = () => {
  const stars = Array.from({ length: 96 }, (_, index) => {
    const x = (index * 83) % 1920;
    const y = 22 + ((index * 53) % 525);
    const size = index % 9 === 0 ? 3 : index % 4 === 0 ? 2 : 1;
    const opacity = 0.16 + (index % 5) * 0.08;
    return { x, y, size, opacity };
  });

  return (
    <AbsoluteFill>
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_72%_52%,rgba(102,116,170,0.20),transparent_28%),linear-gradient(180deg,#090D12_0%,#0C1119_54%,#101124_100%)]" />
      {stars.map((star, index) => (
        <div
          key={index}
          className="absolute rounded-full bg-[#cfd9ff]"
          style={{
            left: star.x,
            top: star.y,
            width: star.size,
            height: star.size,
            opacity: star.opacity,
            boxShadow: star.size > 1 ? "0 0 10px rgba(195,210,255,0.45)" : undefined,
          }}
        />
      ))}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_46%,transparent_0%,rgba(0,0,0,0.46)_100%)]" />
    </AbsoluteFill>
  );
};

const DepthFloor: React.FC = () => (
  <>
    <div className="absolute inset-x-0 bottom-0 h-[480px] bg-[linear-gradient(180deg,transparent_0%,rgba(25,25,62,0.58)_54%,rgba(18,17,43,0.98)_100%)]" />
    <svg
      className="absolute inset-x-0 bottom-0 h-[392px] w-full opacity-70"
      viewBox="0 0 1920 392"
      preserveAspectRatio="none"
    >
      <defs>
        <linearGradient id="floorLine" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="rgba(125,121,255,0)" />
          <stop offset="58%" stopColor="rgba(125,121,255,0.34)" />
          <stop offset="100%" stopColor="rgba(125,121,255,0.68)" />
        </linearGradient>
      </defs>
      {[64, 112, 158, 204, 250, 298, 346, 386].map((y, index) => (
        <line
          key={`h-${index}`}
          x1="0"
          x2="1920"
          y1={y}
          y2={y}
          stroke="rgba(125,121,255,0.30)"
          strokeWidth={index > 5 ? 2 : 1}
        />
      ))}
      {[-900, -620, -390, -190, 0, 190, 390, 620, 900].map((x, index) => (
        <line
          key={`v-${index}`}
          x1="960"
          x2={960 + x}
          y1="46"
          y2="392"
          stroke="url(#floorLine)"
          strokeWidth={x === 0 ? 2 : 1}
        />
      ))}
    </svg>
    <div
      className="absolute inset-x-[-18%] bottom-[-88px] h-[560px] opacity-95"
      style={{
        transform: "perspective(820px) rotateX(66deg)",
        transformOrigin: "50% 100%",
        backgroundImage:
          "linear-gradient(rgba(125,121,255,0.35) 1px, transparent 1px), linear-gradient(90deg, rgba(125,121,255,0.38) 1px, transparent 1px)",
        backgroundSize: "96px 96px",
        maskImage: "linear-gradient(to top, black 0%, black 70%, transparent 100%)",
      }}
    />
    <div className="absolute inset-x-0 bottom-0 h-[180px] bg-[linear-gradient(180deg,transparent,rgba(8,9,18,0.88))]" />
  </>
);

const PointerGlyph: React.FC<{ frame: number }> = ({ frame }) => {
  const y = interpolate(Math.sin(frame / 18), [-1, 1], [-8, 8]);
  return (
    <div
      className="absolute left-[1010px] top-[420px] z-[1000] h-11 w-11"
      style={{ transform: `translateY(${y}px) rotate(-28deg)` }}
    >
      <div className="h-full w-full [clip-path:polygon(50%_0%,100%_100%,54%_76%,0_100%)] bg-[linear-gradient(145deg,#ffcc58_0%,#ff7b32_62%,#9059ff_100%)] shadow-[0_0_22px_rgba(255,137,60,0.38)]" />
    </div>
  );
};

const DepthCard: React.FC<{
  project: Project;
  isHero: boolean;
  style: React.CSSProperties;
}> = ({ project, isHero, style }) => {
  return (
    <article
      className="absolute left-1/2 top-1/2 overflow-hidden rounded-[34px] border border-[#dfe8ff]/45 bg-[#5d6874] shadow-[0_0_44px_rgba(183,204,244,0.18),0_36px_120px_rgba(0,0,0,0.54)]"
      style={{
        ...style,
        transformStyle: "preserve-3d",
      }}
    >
      <div className="absolute inset-[14px] bottom-[128px] overflow-hidden rounded-[26px] bg-[#0e1119]">
        {project.kind === "matcha" ? <MatchaVisual /> : null}
        {project.kind === "mobile" ? <MobileVisual /> : null}
        {project.kind === "transfer" ? <TransferVisual /> : null}
        {project.kind === "dashboard" ? <DashboardVisual /> : null}
      </div>
      <div className="absolute inset-x-0 bottom-0 flex h-[132px] flex-col items-center justify-center bg-[#59636f] px-6 text-center">
        <h2
          className={
            isHero
              ? "font-serif text-[60px] font-black leading-none tracking-[-0.04em] text-white"
              : "text-[27px] font-black leading-none tracking-[-0.04em] text-white"
          }
        >
          {project.title}
        </h2>
        <p className="mt-3 text-[14px] font-black tracking-[0.10em] text-white/[0.92]">
          {project.meta}
        </p>
      </div>
    </article>
  );
};

const MatchaVisual: React.FC = () => (
  <div className="relative h-full bg-[linear-gradient(180deg,#81c5ff_0%,#f5fbff_64%,#d5c9af_100%)]">
    <div className="absolute inset-x-0 top-0 h-1/2 bg-[radial-gradient(circle_at_35%_38%,white_0_5%,transparent_6%),radial-gradient(circle_at_62%_24%,white_0_3%,transparent_4%)] opacity-80" />
    <div className="absolute bottom-9 left-1/2 h-[62px] w-[172px] -translate-x-1/2 rounded-t-[28px] bg-[#dfd7c7]" />
    <div className="absolute bottom-[88px] left-[28%] h-[72px] w-[72px] rounded-[18px] bg-[#242529]" />
    <div className="absolute bottom-[92px] left-[48%] h-[170px] w-[98px] rounded-[18px] bg-[#e8fb3e] shadow-[0_14px_34px_rgba(0,0,0,0.28)]">
      <div className="mx-auto mt-7 h-12 w-12 rounded-full bg-[#d7ed53] ring-2 ring-[#4e6a22]" />
      <div className="mt-5 text-center text-[17px] font-black tracking-[-0.04em] text-[#20230d]">
        Matcha
      </div>
      <div className="mx-auto mt-2 h-2 w-14 rounded-full bg-[#28330f]/35" />
    </div>
  </div>
);

const MobileVisual: React.FC = () => (
  <div className="relative h-full bg-[radial-gradient(circle_at_42%_38%,#f0a0bf_0%,#5c416b_42%,#15121e_100%)]">
    <div className="absolute left-1/2 top-1/2 h-[58%] w-[42%] -translate-x-1/2 -translate-y-1/2 rounded-[24px] border border-white/20 bg-[#171520] p-3">
      <div className="mx-auto h-3 w-14 rounded-full bg-white/15" />
      <div className="mt-5 h-20 rounded-2xl bg-[linear-gradient(145deg,#f99bd0,#764cff)]" />
      <div className="mt-4 space-y-3">
        {[0, 1, 2].map((item) => (
          <div key={item} className="h-8 rounded-xl bg-white/10" />
        ))}
      </div>
    </div>
  </div>
);

const TransferVisual: React.FC = () => (
  <div className="relative h-full bg-[#202737]">
    <div className="absolute inset-0 bg-[linear-gradient(145deg,#c4dbff_0%,#edf4ff_44%,#a7bce0_100%)]" />
    <div className="absolute right-8 top-[18%] h-[68%] w-[57%] rounded-[18px] bg-[#171b25] p-7 shadow-[0_22px_64px_rgba(0,0,0,0.34)]">
      <div className="mb-14 flex gap-3">
        <span className="h-4 w-4 rounded-full bg-black/35" />
        <span className="h-4 w-4 rounded-full bg-black/35" />
        <span className="h-4 w-4 rounded-full bg-black/35" />
      </div>
      <div className="flex items-center gap-5">
        <div className="grid h-14 w-14 place-items-center rounded-2xl bg-[#adff8d] text-[35px] text-black">
          +
        </div>
        <div>
          <div className="font-serif text-[33px] font-black leading-none">Send files</div>
          <div className="mt-2 font-mono text-[15px] text-white/55">155,5 GB available</div>
        </div>
      </div>
      <div className="mt-16 font-mono text-[15px] uppercase tracking-[0.10em] text-white/45">
        Previous Transfers
      </div>
      <div className="mt-7 space-y-4">
        {["Team Picasso", "Maryan Humenetsky", "Photoshoots", "Lilly Appel"].map(
          (name, index) => (
            <div
              key={name}
              className={`flex items-center gap-4 rounded-2xl px-4 py-3 ${
                index === 1 ? "bg-white/10" : ""
              }`}
            >
              <div className="h-9 w-9 rounded-xl bg-[linear-gradient(135deg,#eeb1b7,#b3fff6)]" />
              <div>
                <div className="text-[18px] font-black">{name}</div>
                <div className="font-mono text-[13px] text-white/46">Demo_Final.mov</div>
              </div>
            </div>
          ),
        )}
      </div>
    </div>
  </div>
);

const DashboardVisual: React.FC = () => (
  <div className="h-full bg-[#f3efe7] p-8 text-[#14161b]">
    <div className="text-[30px] font-black">Landlord OS</div>
    <div className="mt-8 grid grid-cols-3 gap-4">
      {[78, 52, 91].map((value) => (
        <div key={value} className="rounded-2xl bg-white p-5 shadow-[0_8px_20px_rgba(0,0,0,0.08)]">
          <div className="text-[13px] text-black/30">Yield</div>
          <div className="mt-5 text-[34px] font-black">{value}</div>
        </div>
      ))}
    </div>
    <div className="mt-7 flex h-32 items-end gap-4 rounded-3xl bg-white p-5">
      {[42, 82, 58, 106, 73, 132].map((height, index) => (
        <div key={index} className="flex-1 rounded-t-lg bg-[#121620]" style={{ height }} />
      ))}
    </div>
  </div>
);
