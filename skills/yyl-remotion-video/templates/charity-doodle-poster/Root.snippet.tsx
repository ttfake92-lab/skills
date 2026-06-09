import { Composition } from "remotion";
import { CharityDoodlePoster } from "./CharityDoodlePoster";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="CharityDoodlePoster"
      component={CharityDoodlePoster}
      durationInFrames={132}
      fps={60}
      width={1920}
      height={1080}
    />
  );
};
