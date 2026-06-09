import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

type PaletteId = "zoo-yellow" | "sky-blue" | "soft-peach" | "lime-green" | "rose-pink";

type PosterPalette = {
  id: PaletteId;
  background: string;
  ink: string;
  button: string;
};

const palettes: PosterPalette[] = [
  { id: "zoo-yellow", background: "#E8F582", ink: "#050505", button: "#FAFAF4" },
  { id: "sky-blue", background: "#93BDED", ink: "#050505", button: "#F8FBFF" },
  { id: "soft-peach", background: "#F1B794", ink: "#050505", button: "#FFF8F2" },
  { id: "lime-green", background: "#D7F28C", ink: "#050505", button: "#FCFFF4" },
  { id: "rose-pink", background: "#EF8E90", ink: "#050505", button: "#FFF6F6" },
];

export type CharityDoodlePosterProps = {
  paletteId?: PaletteId;
  headline?: string;
  body?: string;
};

const defaultBody =
  "Ukrainian zoos are closed\nbecause of war. We can't visit\nanimals yet, but we can help\nraise money to feed them.";

const posterDuration = 132;

export const CharityDoodlePoster: React.FC<CharityDoodlePosterProps> = ({
  paletteId = "zoo-yellow",
  headline = "FEED THE ZOO",
  body = defaultBody,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const palette =
    palettes.find((candidate) => candidate.id === paletteId) ?? palettes[0];
  const boilSeed = Math.floor(frame / 3) + 17;
  const boilTick = Math.floor(frame / 3);
  const tinyShakeX = ((boilTick * 17) % 7) - 3;
  const tinyShakeY = ((boilTick * 23) % 5) - 2;
  const reveal = spring({
    frame: frame - 12,
    fps,
    durationInFrames: 52,
    config: {
      damping: 24,
      mass: 1.25,
      stiffness: 68,
    },
  });
  const animalScale = interpolate(reveal, [0, 1], [0.34, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
  const animalX = interpolate(reveal, [0, 1], [1120, 920], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const animalY = interpolate(reveal, [0, 1], [590, 650], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const animalOpacity = interpolate(frame, [6, 20], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const titleLift = interpolate(frame, [0, posterDuration - 1], [0, -5], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      className="overflow-hidden"
      style={{ backgroundColor: palette.background, color: palette.ink }}
    >
      <svg
        className="absolute inset-0 h-full w-full"
        viewBox="0 0 1920 1080"
        role="img"
        aria-label={headline}
      >
        <defs>
          <filter id="line-boil" x="-20%" y="-20%" width="140%" height="140%">
            <feTurbulence
              type="fractalNoise"
              baseFrequency="0.012"
              numOctaves="3"
              seed={boilSeed}
              result="noise"
            />
            <feDisplacementMap
              in="SourceGraphic"
              in2="noise"
              scale="4"
              xChannelSelector="R"
              yChannelSelector="G"
              result="boiled"
            />
            <feGaussianBlur in="boiled" stdDeviation="0.65" result="softInk" />
            <feComponentTransfer in="softInk">
              <feFuncA type="gamma" amplitude="1.5" exponent="0.62" offset="0" />
            </feComponentTransfer>
          </filter>
          <filter id="button-shadow" x="-40%" y="-40%" width="180%" height="180%">
            <feDropShadow dx="0" dy="2" stdDeviation="1.4" floodOpacity="0.25" />
          </filter>
        </defs>

        <g filter="url(#line-boil)" transform={`translate(${tinyShakeX} ${tinyShakeY})`}>
          <Headline yOffset={titleLift} ink={palette.ink} />
          <DescriptionText body={body} ink={palette.ink} />
          <g
            opacity={animalOpacity}
            transform={`translate(${animalX} ${animalY}) scale(${animalScale}) translate(-960 -540)`}
          >
            <ChimpIllustration ink={palette.ink} />
          </g>
        </g>

        <g filter="url(#button-shadow)">
          <circle cx="102" cy="992" r="66" fill={palette.button} stroke={palette.ink} strokeWidth="1.5" />
          <g filter="url(#line-boil)" stroke={palette.ink} strokeWidth="4" strokeLinecap="round">
            <line x1="102" x2="102" y1="974" y2="1010" />
            <line x1="84" x2="120" y1="992" y2="992" />
          </g>
        </g>
      </svg>
    </AbsoluteFill>
  );
};

const Headline: React.FC<{ yOffset: number; ink: string }> = ({ yOffset, ink }) => (
  <g fill={ink} transform={`translate(35 ${174 + yOffset})`}>
    <text
      x="0"
      y="0"
      fontFamily="Arial Black, Helvetica, sans-serif"
      fontSize="208"
      fontWeight="900"
      letterSpacing="-9"
      dominantBaseline="alphabetic"
    >
      FEED THE Z
    </text>
    <OrganicO cx={1526} cy={-62} rx={76} ry={89} rotate={-13} ink={ink} />
    <OrganicO cx={1628} cy={-62} rx={78} ry={91} rotate={8} ink={ink} />
  </g>
);

const OrganicO: React.FC<{
  cx: number;
  cy: number;
  rx: number;
  ry: number;
  rotate: number;
  ink: string;
}> = ({ cx, cy, rx, ry, rotate, ink }) => (
  <g transform={`translate(${cx} ${cy}) rotate(${rotate})`}>
    <ellipse
      cx="0"
      cy="0"
      rx={rx}
      ry={ry}
      fill="none"
      stroke={ink}
      strokeWidth="17"
      strokeLinecap="round"
    />
    <ellipse
      cx="5"
      cy="2"
      rx={rx - 7}
      ry={ry - 9}
      fill="none"
      stroke={ink}
      strokeWidth="5"
      opacity="0.55"
      strokeLinecap="round"
    />
  </g>
);

const DescriptionText: React.FC<{ body: string; ink: string }> = ({ body, ink }) => (
  <text
    x="38"
    y="272"
    fill={ink}
    fontFamily="Inter, Helvetica, Arial, sans-serif"
    fontSize="31"
    fontWeight="500"
    letterSpacing="-0.8"
  >
    {body.split("\n").map((line, index) => (
      <tspan key={line} x="38" dy={index === 0 ? 0 : 39}>
        {line}
      </tspan>
    ))}
  </text>
);

const ChimpIllustration: React.FC<{ ink: string }> = ({ ink }) => {
  const stroke = {
    fill: "none",
    stroke: ink,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  };

  return (
    <g>
      <path
        {...stroke}
        strokeWidth="54"
        d="M475 1050 C500 875 560 735 640 590 C700 480 730 380 710 285 C690 195 750 130 840 125 C945 120 1012 182 1002 292"
      />
      <path
        {...stroke}
        strokeWidth="51"
        d="M1215 1044 C1185 870 1125 735 1030 612 C962 524 930 420 962 305 C995 185 1080 136 1174 172 C1276 212 1328 316 1286 428"
      />
      <path
        {...stroke}
        strokeWidth="56"
        d="M640 610 C675 500 790 440 937 458 C1088 477 1195 568 1186 690 C1176 826 1042 895 878 870 C720 846 608 741 640 610 Z"
      />
      <path
        {...stroke}
        strokeWidth="34"
        d="M804 430 C770 350 788 268 858 238 C930 207 1004 247 1018 333"
      />
      <path
        {...stroke}
        strokeWidth="31"
        d="M1038 338 C1077 268 1155 248 1210 296 C1268 347 1254 430 1198 494"
      />
      <path
        {...stroke}
        strokeWidth="34"
        d="M1016 858 C1124 888 1240 975 1312 1075"
      />
      <path
        {...stroke}
        strokeWidth="28"
        d="M665 792 C592 858 528 945 482 1072"
      />
      <path {...stroke} strokeWidth="18" d="M810 610 C865 575 925 566 978 592" opacity="0.65" />
      <path {...stroke} strokeWidth="13" d="M760 552 L760 552" />
      <path {...stroke} strokeWidth="13" d="M914 544 L914 544" />
      <path {...stroke} strokeWidth="13" d="M814 675 L814 675" />
      <path {...stroke} strokeWidth="13" d="M925 668 L925 668" />

      <path
        {...stroke}
        strokeWidth="12"
        opacity="0.45"
        d="M450 1036 C500 860 540 752 622 604"
      />
      <path
        {...stroke}
        strokeWidth="10"
        opacity="0.35"
        d="M616 636 C690 516 805 492 936 500 C1052 509 1158 590 1154 696"
      />
      <path
        {...stroke}
        strokeWidth="11"
        opacity="0.38"
        d="M1232 1032 C1198 880 1140 750 1046 630"
      />
    </g>
  );
};
