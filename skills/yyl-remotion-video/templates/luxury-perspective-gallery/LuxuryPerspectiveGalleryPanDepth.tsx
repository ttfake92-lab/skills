import React from "react";
import {
  AbsoluteFill,
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

type DepthSlot = {
  x: number;
  y: number;
  width: number;
  height: number;
  opacity: number;
  blur: number;
  glow: number;
};

const holdSeconds = 2;
const moveSeconds = 0.8;

const projects: Project[] = [
  {
    title: "Droppable",
    meta: "DESKTOP APP * 2023",
    kind: "transfer",
  },
  {
    title: "SummerRain",
    meta: "DTC BRAND * 2022",
    kind: "matcha",
  },
  {
    title: "Wunderflats App",
    meta: "MOBILE APP * 2022",
    kind: "mobile",
  },
  {
    title: "Landlord Dashboard",
    meta: "WEB APP * 2019-2022",
    kind: "dashboard",
  },
];

const slots = {
  featuredLeft: {
    x: 386,
    y: 450,
    width: 520,
    height: 690,
    opacity: 1,
    blur: 0,
    glow: 1,
  },
  featuredRight: {
    x: 1534,
    y: 450,
    width: 520,
    height: 690,
    opacity: 1,
    blur: 0,
    glow: 1,
  },
  exitFrontLeft: {
    x: -250,
    y: 650,
    width: 760,
    height: 1010,
    opacity: 0,
    blur: 0,
    glow: 0.65,
  },
  exitFrontRight: {
    x: 2170,
    y: 650,
    width: 760,
    height: 1010,
    opacity: 0,
    blur: 0,
    glow: 0.65,
  },
  midLeft: {
    x: 810,
    y: 510,
    width: 238,
    height: 330,
    opacity: 0.92,
    blur: 0,
    glow: 0.7,
  },
  midRight: {
    x: 1110,
    y: 510,
    width: 238,
    height: 330,
    opacity: 0.92,
    blur: 0,
    glow: 0.7,
  },
  centerBack: {
    x: 960,
    y: 430,
    width: 138,
    height: 205,
    opacity: 0.26,
    blur: 8,
    glow: 0.12,
  },
  deepestBack: {
    x: 960,
    y: 350,
    width: 54,
    height: 82,
    opacity: 0,
    blur: 16,
    glow: 0,
  },
} satisfies Record<string, DepthSlot>;

const mix = (from: number, to: number, progress: number) =>
  interpolate(progress, [0, 1], [from, to], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

const mixSlot = (from: DepthSlot, to: DepthSlot, progress: number): DepthSlot => ({
  x: mix(from.x, to.x, progress),
  y: mix(from.y, to.y, progress),
  width: mix(from.width, to.width, progress),
  height: mix(from.height, to.height, progress),
  opacity: mix(from.opacity, to.opacity, progress),
  blur: mix(from.blur, to.blur, progress),
  glow: mix(from.glow, to.glow, progress),
});

const getSlot = (projectIndex: number, stageIndex: number): DepthSlot => {
  const relation = (projectIndex - stageIndex + projects.length) % projects.length;
  const focusOnLeft = stageIndex % 2 === 0;

  if (relation === 0) {
    return focusOnLeft ? slots.featuredLeft : slots.featuredRight;
  }

  if (relation === 1) {
    return focusOnLeft ? slots.midRight : slots.midLeft;
  }

  if (relation === 2) {
    return slots.centerBack;
  }

  return slots.deepestBack;
};

const getTransitionTargetSlot = (
  projectIndex: number,
  stageIndex: number,
): DepthSlot => {
  const relation = (projectIndex - stageIndex + projects.length) % projects.length;
  const focusOnLeft = stageIndex % 2 === 0;

  if (relation === 0) {
    return focusOnLeft ? slots.exitFrontLeft : slots.exitFrontRight;
  }

  return getSlot(projectIndex, (stageIndex + 1) % projects.length);
};

export const LuxuryPerspectiveGalleryPanDepth: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const holdFrames = Math.round(fps * holdSeconds);
  const moveFrames = Math.round(fps * moveSeconds);
  const stageFrames = holdFrames + moveFrames;
  const loopFrames = projects.length * stageFrames;
  const loopFrame = frame % loopFrames;
  const stageIndex = Math.floor(loopFrame / stageFrames);
  const stageFrame = loopFrame % stageFrames;
  const rawMoveFrame = Math.max(0, stageFrame - holdFrames);
  const moving = stageFrame >= holdFrames;
  const moveProgress = moving
    ? spring({
        frame: rawMoveFrame,
        fps,
        durationInFrames: moveFrames,
        config: {
          damping: 28,
          mass: 1.15,
          stiffness: 70,
        },
      })
    : 0;

  return (
    <AbsoluteFill className="overflow-hidden bg-[#090D12] text-white">
      <PanStageBackground />
      <PanHeader />
      <main className="absolute inset-0 overflow-hidden">
        {projects.map((project, projectIndex) => (
          <PanCard
            key={project.title}
            project={project}
            projectIndex={projectIndex}
            stageIndex={stageIndex}
            moveProgress={moveProgress}
          />
        ))}
      </main>
      <button className="absolute bottom-[32px] left-1/2 z-[2000] h-[58px] w-[174px] -translate-x-1/2 rounded-[18px] border border-white/[0.65] bg-[linear-gradient(180deg,#edf4ff_0%,#b8c2d9_100%)] text-[13px] font-black tracking-[0.10em] text-[#171d2a] shadow-[0_0_28px_rgba(159,178,255,0.30),inset_0_1px_0_rgba(255,255,255,0.9)]">
        SAY HELLO
      </button>
    </AbsoluteFill>
  );
};

const PanCard: React.FC<{
  project: Project;
  projectIndex: number;
  stageIndex: number;
  moveProgress: number;
}> = ({
  project,
  projectIndex,
  stageIndex,
  moveProgress,
}) => {
  const currentSlot = getSlot(projectIndex, stageIndex);
  const nextSlot = getTransitionTargetSlot(projectIndex, stageIndex);
  const { x, y, width, height, opacity, blur, glow } = mixSlot(
    currentSlot,
    nextSlot,
    moveProgress,
  );
  const depth = width * (opacity + glow * 0.2);

  return (
    <article
      className="absolute overflow-hidden rounded-[34px] border border-[#dfe8ff]/45 bg-[#59636f]"
      style={{
        left: x,
        top: y,
        width,
        height,
        opacity,
        zIndex: Math.round(depth),
        filter: `blur(${blur}px)`,
        transform: "translate(-50%, -50%)",
        boxShadow: `0 0 ${28 + glow * 44}px rgba(182,204,244,${0.08 + glow * 0.18}), 0 28px 90px rgba(0,0,0,0.48)`,
      }}
    >
      <div className="absolute inset-[14px] bottom-[92px] overflow-hidden rounded-[25px] bg-[#111720]">
        {project.kind === "matcha" ? <MatchaPanel /> : null}
        {project.kind === "mobile" ? <MobilePanel /> : null}
        {project.kind === "transfer" ? <TransferPanel /> : null}
        {project.kind === "dashboard" ? <DashboardPanel /> : null}
      </div>
      <div className="absolute inset-x-0 bottom-0 flex h-[104px] flex-col items-center justify-center bg-[#59636f] px-5 text-center">
        <h2
          className={
            width >= 500
              ? "font-serif text-[46px] font-black leading-none tracking-[-0.04em]"
              : "text-[22px] font-black leading-none tracking-[-0.04em]"
          }
        >
          {project.title}
        </h2>
        <p className="mt-2 text-[11px] font-black tracking-[0.12em] text-white/[0.88]">
          {project.meta}
        </p>
      </div>
    </article>
  );
};

const PanHeader: React.FC = () => (
  <header className="absolute left-0 right-0 top-[42px] z-[2000] flex justify-center">
    <div className="flex items-center gap-3 text-[18px] font-black tracking-[0.04em] text-white">
      <div className="grid h-[36px] w-[36px] place-items-center rounded-[12px] border border-white/[0.22] bg-[#f2f4f8] text-[18px] font-black text-[#141a25] shadow-[0_0_20px_rgba(208,222,255,0.20)]">
        鱼
      </div>
      <span>鱼亦乐</span>
    </div>
  </header>
);

const PanStageBackground: React.FC = () => {
  const stars = Array.from({ length: 120 }, (_, index) => ({
    x: (index * 89) % 1920,
    y: 28 + ((index * 47) % 505),
    size: index % 10 === 0 ? 2.6 : index % 4 === 0 ? 1.7 : 1,
    opacity: 0.12 + (index % 5) * 0.07,
  }));

  return (
    <AbsoluteFill>
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_78%_48%,rgba(94,112,165,0.16),transparent_28%),linear-gradient(180deg,#090D12_0%,#0A0F16_50%,#111126_100%)]" />
      {stars.map((star, index) => (
        <div
          key={index}
          className="absolute rounded-full bg-[#d7e1ff]"
          style={{
            left: star.x,
            top: star.y,
            width: star.size,
            height: star.size,
            opacity: star.opacity,
          }}
        />
      ))}
      <div className="absolute inset-x-0 bottom-0 h-[455px] bg-[linear-gradient(180deg,transparent_0%,rgba(22,22,58,0.70)_58%,rgba(17,16,39,0.98)_100%)]" />
      <svg
        className="absolute inset-x-0 bottom-0 h-[385px] w-full opacity-80"
        viewBox="0 0 1920 385"
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient id="panFloorLine" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="rgba(125,121,255,0)" />
            <stop offset="55%" stopColor="rgba(125,121,255,0.34)" />
            <stop offset="100%" stopColor="rgba(125,121,255,0.70)" />
          </linearGradient>
        </defs>
        {[48, 92, 136, 180, 226, 274, 324, 374].map((y, index) => (
          <line
            key={`h-${index}`}
            x1="0"
            x2="1920"
            y1={y}
            y2={y}
            stroke="rgba(125,121,255,0.28)"
            strokeWidth={index > 5 ? 2 : 1}
          />
        ))}
        {[-940, -690, -470, -260, -92, 92, 260, 470, 690, 940].map((x, index) => (
          <line
            key={`v-${index}`}
            x1="960"
            x2={960 + x}
            y1="42"
            y2="385"
            stroke="url(#panFloorLine)"
            strokeWidth={Math.abs(x) === 92 ? 2 : 1}
          />
        ))}
      </svg>
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_48%,transparent_0%,rgba(0,0,0,0.36)_100%)]" />
    </AbsoluteFill>
  );
};

const MatchaPanel: React.FC = () => (
  <div className="relative h-full bg-[linear-gradient(180deg,#7fc5ff_0%,#eaf7ff_58%,#d9d0bf_100%)]">
    <div className="absolute inset-x-0 top-0 h-1/2 bg-[radial-gradient(circle_at_36%_34%,white_0_5%,transparent_6%),radial-gradient(circle_at_62%_24%,white_0_3%,transparent_4%)] opacity-75" />
    <div className="absolute bottom-6 left-1/2 h-[58px] w-[174px] -translate-x-1/2 rounded-t-[28px] bg-[#ddd4c2]" />
    <div className="absolute bottom-[82px] left-[30%] h-[70px] w-[70px] rounded-[18px] bg-[#242529]" />
    <div className="absolute bottom-[82px] left-[50%] h-[176px] w-[102px] rounded-[18px] bg-[#e8fb3e] shadow-[0_14px_34px_rgba(0,0,0,0.28)]">
      <div className="mx-auto mt-7 h-12 w-12 rounded-full bg-[#d7ed53] ring-2 ring-[#4e6a22]" />
      <div className="mt-5 text-center text-[18px] font-black tracking-[-0.04em] text-[#20230d]">
        Matcha
      </div>
      <div className="mx-auto mt-2 h-2 w-14 rounded-full bg-[#28330f]/35" />
    </div>
  </div>
);

const MobilePanel: React.FC = () => (
  <div className="relative h-full bg-[radial-gradient(circle_at_42%_38%,#ffbfd3_0%,#f2a8c9_30%,#8c5674_58%,#412f56_100%)]">
    <div className="absolute right-0 top-0 h-full w-[45%] bg-[#f39cc7]" />
    <div className="absolute left-[18%] top-[15%] h-[70%] w-[54%] rounded-[30px] border border-[#15151e]/30 bg-[#f7ecff] p-4 shadow-[0_20px_56px_rgba(0,0,0,0.28)]">
      <div className="mx-auto h-3 w-20 rounded-full bg-black/20" />
      <div className="mt-5 h-16 rounded-2xl bg-white" />
      <div className="mt-4 space-y-3">
        {[0, 1, 2].map((item) => (
          <div key={item} className="h-9 rounded-xl bg-[#20202a]/12" />
        ))}
      </div>
    </div>
  </div>
);

const TransferPanel: React.FC = () => (
  <div className="relative h-full bg-[linear-gradient(145deg,#c7ddff_0%,#eef4ff_44%,#a9bddd_100%)]">
    <div className="absolute right-[6%] top-[18%] h-[68%] w-[58%] rounded-[18px] bg-[#171b25] p-7 shadow-[0_22px_64px_rgba(0,0,0,0.34)]">
      <div className="mb-12 flex gap-3">
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
      <div className="mt-14 font-mono text-[15px] uppercase tracking-[0.10em] text-white/45">
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

const DashboardPanel: React.FC = () => (
  <div className="h-full bg-[#f3efe7] p-7 text-[#14161b]">
    <div className="grid h-full grid-cols-[0.62fr_1fr] gap-5">
      <div className="overflow-hidden rounded-3xl bg-[linear-gradient(135deg,#d6c8b5,#ffffff)]" />
      <div className="rounded-3xl bg-white p-5">
        <div className="text-[20px] font-black">Inbox</div>
        <div className="mt-6 space-y-4">
          {[0, 1, 2, 3].map((item) => (
            <div key={item} className="h-9 rounded-xl bg-[#191a22]/10" />
          ))}
        </div>
      </div>
    </div>
  </div>
);
