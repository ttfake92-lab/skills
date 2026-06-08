import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

type ProjectKind = "packaging" | "dashboard" | "mobile";

type Project = {
  title: string;
  eyebrow: string;
  description: string;
  kind: ProjectKind;
};

const projects: Project[] = [
  {
    title: "SummerRain",
    eyebrow: "01 / PACKAGING",
    description: "Lime citrus identity system",
    kind: "packaging",
  },
  {
    title: "Landlord Dashboard",
    eyebrow: "02 / PRODUCT",
    description: "Rental operations interface",
    kind: "dashboard",
  },
  {
    title: "Wunderflats App",
    eyebrow: "03 / MOBILE",
    description: "Premium relocation experience",
    kind: "mobile",
  },
];

const loopDistance = (index: number, center: number, total: number) => {
  let diff = index - (center % total);
  if (diff > total / 2) diff -= total;
  if (diff < -total / 2) diff += total;
  return diff;
};

const clampInput = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};

export const LuxuryPerspectiveGallery: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const holdFrames = fps * 1.2;
  const moveFrames = fps * 1.15;
  const cycleFrames = holdFrames + moveFrames;
  const cycleIndex = Math.floor(frame / cycleFrames);
  const cycleFrame = frame % cycleFrames;
  const moveProgress =
    cycleFrame < holdFrames
      ? 0
      : spring({
          frame: cycleFrame - holdFrames,
          fps,
          config: {
            damping: 24,
            stiffness: 86,
            mass: 1.15,
          },
        });

  const easedProgress = interpolate(moveProgress, [0, 1], [0, 1], {
    ...clampInput,
    easing: Easing.bezier(0.65, 0, 0.35, 1),
  });
  const virtualCenter = cycleIndex + easedProgress;

  return (
    <AbsoluteFill className="overflow-hidden bg-[#0D0E12] text-white">
      <SpaceBackground />
      <Header />

      <main className="absolute inset-x-0 top-[132px] bottom-[118px] flex items-center justify-center">
        <div
          className="relative h-[650px] w-full"
          style={{
            perspective: 1500,
            transformStyle: "preserve-3d",
          }}
        >
          {projects.map((project, index) => {
            const distance = loopDistance(index, virtualCenter, projects.length);
            const abs = Math.abs(distance);
            const rotateY = interpolate(distance, [-1.5, 0, 1.5], [32, 0, -32], {
              ...clampInput,
              easing: Easing.bezier(0.65, 0, 0.35, 1),
            });
            const scale = interpolate(abs, [0, 1.5], [1, 0.82], clampInput);
            const opacity = interpolate(abs, [0, 1.5], [1, 0.46], clampInput);
            const translateX = distance * 430;
            const translateZ = interpolate(abs, [0, 1.5], [80, -230], clampInput);
            const blur = interpolate(abs, [0, 1.5], [0, 2.2], clampInput);

            return (
              <ProjectCard
                key={project.title}
                project={project}
                style={{
                  opacity,
                  zIndex: Math.round(100 - abs * 30),
                  filter: `blur(${blur}px)`,
                  transform: [
                    "translate(-50%, -50%)",
                    `translateX(${translateX}px)`,
                    `translateZ(${translateZ}px)`,
                    `rotateY(${rotateY}deg)`,
                    `scale(${scale})`,
                  ].join(" "),
                }}
              />
            );
          })}
        </div>
      </main>

      <button className="absolute bottom-10 left-1/2 -translate-x-1/2 rounded-full border border-violet-300/35 bg-white/[0.035] px-12 py-5 text-[18px] font-semibold tracking-[0.28em] text-violet-50 shadow-[0_0_48px_rgba(129,92,255,0.30)] backdrop-blur-xl">
        SAY HELLO
      </button>
    </AbsoluteFill>
  );
};

const Header: React.FC = () => {
  return (
    <header className="absolute left-0 right-0 top-0 z-[200] flex h-[104px] items-center justify-between px-[74px]">
      <button className="rounded-full border border-white/10 bg-white/[0.055] px-6 py-3 text-[15px] font-medium text-white/[0.78] backdrop-blur-xl">
        Index
      </button>
      <div className="flex items-center gap-3 rounded-full border border-white/10 bg-white/[0.05] px-4 py-2.5 backdrop-blur-xl">
        <div className="h-9 w-9 rounded-full bg-[radial-gradient(circle_at_35%_30%,#fff_0,#d8c8ff_26%,#7857ff_60%,#16121f_100%)] shadow-[0_0_22px_rgba(139,92,246,0.42)]" />
        <span className="text-[16px] font-semibold text-white/[0.86]">Roman</span>
      </div>
      <button className="rounded-full bg-white px-6 py-3 text-[15px] font-semibold text-[#111217] shadow-[0_14px_38px_rgba(255,255,255,0.14)]">
        Subscribe
      </button>
    </header>
  );
};

const SpaceBackground: React.FC = () => {
  return (
    <AbsoluteFill>
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_22%,rgba(96,76,255,0.28),transparent_30%),linear-gradient(180deg,#0D0E12_0%,#11131B_52%,#080910_100%)]" />
      <div className="absolute inset-x-0 bottom-0 h-[470px] bg-[radial-gradient(ellipse_at_center,rgba(127,83,255,0.22),transparent_58%)]" />
      <div
        className="absolute inset-x-[-10%] bottom-[-18%] h-[470px] opacity-55"
        style={{
          transform: "perspective(800px) rotateX(62deg)",
          backgroundImage:
            "linear-gradient(rgba(147,129,255,0.18) 1px, transparent 1px), linear-gradient(90deg, rgba(147,129,255,0.16) 1px, transparent 1px)",
          backgroundSize: "86px 86px",
          maskImage: "linear-gradient(to top, black 0%, black 48%, transparent 100%)",
        }}
      />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,transparent_0%,rgba(0,0,0,0.62)_100%)]" />
    </AbsoluteFill>
  );
};

const ProjectCard: React.FC<{
  project: Project;
  style: React.CSSProperties;
}> = ({ project, style }) => {
  return (
    <article
      className="absolute left-1/2 top-1/2 h-[610px] w-[520px] overflow-hidden rounded-[24px] border border-white/[0.12] bg-white/10 shadow-[0_34px_110px_rgba(0,0,0,0.52)]"
      style={{
        ...style,
        transformStyle: "preserve-3d",
      }}
    >
      {project.kind === "packaging" ? <PackagingMockup /> : null}
      {project.kind === "dashboard" ? <DashboardMockup /> : null}
      {project.kind === "mobile" ? <MobileMockup /> : null}

      <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/[0.72] via-black/30 to-transparent p-8">
        <p className="mb-3 text-[13px] font-semibold tracking-[0.24em] text-white/[0.58]">
          {project.eyebrow}
        </p>
        <h2 className="text-[38px] font-semibold leading-none tracking-[-0.03em]">
          {project.title}
        </h2>
        <p className="mt-3 text-[17px] text-white/[0.66]">{project.description}</p>
      </div>
    </article>
  );
};

const PackagingMockup: React.FC = () => (
  <div className="relative h-full bg-[#16171b]">
    <div className="absolute inset-y-0 left-0 w-1/2 bg-[#111217]" />
    <div className="absolute inset-y-0 right-0 w-1/2 bg-[#d6ff38]" />
    <div className="absolute left-[82px] top-[80px] h-[345px] w-[174px] rounded-[34px] bg-[#ecff73] shadow-[0_30px_70px_rgba(0,0,0,0.38)]">
      <div className="absolute left-1/2 top-8 h-8 w-20 -translate-x-1/2 rounded-full bg-[#14150f]" />
      <div className="absolute inset-x-7 top-28 text-center text-[52px] font-black leading-[0.86] tracking-[-0.07em] text-[#15160f]">
        SUM
        <br />
        MER
      </div>
      <div className="absolute bottom-10 left-1/2 h-20 w-20 -translate-x-1/2 rounded-full bg-[#78d900]" />
    </div>
    <div className="absolute right-[70px] top-[118px] h-[260px] w-[180px] rounded-[28px] border border-black/10 bg-white/[0.85] p-6 text-[#151515] shadow-[0_20px_58px_rgba(0,0,0,0.20)]">
      <div className="h-3 w-24 rounded-full bg-[#151515]" />
      <div className="mt-8 grid grid-cols-2 gap-3">
        <div className="h-24 rounded-2xl bg-[#d6ff38]" />
        <div className="h-24 rounded-2xl bg-[#1b1d22]" />
      </div>
      <div className="mt-7 h-2 w-28 rounded-full bg-black/18" />
      <div className="mt-3 h-2 w-20 rounded-full bg-black/12" />
    </div>
  </div>
);

const DashboardMockup: React.FC = () => (
  <div className="h-full bg-[#f7f3ea] p-8 text-[#15161a]">
    <div className="mb-7 flex items-center justify-between">
      <div>
        <div className="text-[14px] font-semibold uppercase tracking-[0.2em] text-black/[0.35]">
          Portfolio
        </div>
        <div className="mt-2 text-[34px] font-semibold tracking-[-0.05em]">
          Landlord OS
        </div>
      </div>
      <div className="h-12 w-12 rounded-full bg-[#15161a]" />
    </div>
    <div className="grid grid-cols-3 gap-4">
      {[78, 52, 91].map((value) => (
        <div key={value} className="rounded-3xl border border-black/10 bg-white p-5">
          <div className="text-[13px] text-black/[0.38]">Yield</div>
          <div className="mt-5 text-[38px] font-semibold tracking-[-0.06em]">
            {value}
          </div>
        </div>
      ))}
    </div>
    <div className="mt-5 rounded-[28px] border border-black/10 bg-white p-6">
      <div className="mb-5 flex items-end justify-between">
        <div className="text-[21px] font-semibold tracking-[-0.04em]">Revenue</div>
        <div className="text-[13px] text-black/[0.38]">Q2 / 2026</div>
      </div>
      <div className="flex h-[170px] items-end gap-4 border-b border-black/10">
        {[42, 74, 58, 96, 68, 112, 86].map((height, index) => (
          <div
            key={index}
            className="flex-1 rounded-t-xl bg-[#14161c]"
            style={{ height }}
          />
        ))}
      </div>
    </div>
  </div>
);

const MobileMockup: React.FC = () => (
  <div className="relative h-full bg-[radial-gradient(circle_at_70%_18%,rgba(255,127,179,0.42),transparent_32%),linear-gradient(135deg,#151026_0%,#271235_48%,#090912_100%)]">
    <div className="absolute left-1/2 top-[68px] h-[390px] w-[206px] -translate-x-1/2 rounded-[42px] border border-white/[0.18] bg-[#0f0d19] p-4 shadow-[0_28px_80px_rgba(0,0,0,0.46)]">
      <div className="mx-auto mb-5 h-5 w-20 rounded-full bg-white/8" />
      <div className="rounded-[30px] bg-[linear-gradient(145deg,#ff8ab8,#7e57ff)] p-5">
        <div className="h-20 rounded-3xl bg-white/20" />
        <div className="mt-5 h-3 w-24 rounded-full bg-white/60" />
        <div className="mt-3 h-3 w-16 rounded-full bg-white/[0.32]" />
      </div>
      <div className="mt-5 space-y-3">
        {[0, 1, 2].map((item) => (
          <div key={item} className="rounded-2xl bg-white/[0.075] p-4">
            <div className="h-2 w-20 rounded-full bg-white/[0.36]" />
            <div className="mt-3 h-2 w-32 rounded-full bg-white/[0.14]" />
          </div>
        ))}
      </div>
    </div>
    <div className="absolute right-10 top-20 h-28 w-28 rounded-full bg-[#ff8ab8]/20 blur-2xl" />
    <div className="absolute bottom-28 left-16 h-36 w-36 rounded-full bg-[#715bff]/24 blur-3xl" />
  </div>
);
