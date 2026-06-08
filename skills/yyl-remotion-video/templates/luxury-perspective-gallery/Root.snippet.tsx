import { Composition } from "remotion";
import { LuxuryPerspectiveGallery } from "./LuxuryPerspectiveGallery";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="LuxuryPerspectiveGallery"
      component={LuxuryPerspectiveGallery}
      durationInFrames={360}
      fps={60}
      width={1920}
      height={1080}
    />
  );
};
