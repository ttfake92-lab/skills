import { Composition } from "remotion";
import { LuxuryPerspectiveGallery } from "./LuxuryPerspectiveGallery";
import { LuxuryPerspectiveGalleryPanDepth } from "./LuxuryPerspectiveGalleryPanDepth";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="LuxuryPerspectiveGallery"
        component={LuxuryPerspectiveGallery}
        durationInFrames={360}
        fps={60}
        width={1920}
        height={1080}
      />
      <Composition
        id="LuxuryPerspectiveGalleryPanDepth"
        component={LuxuryPerspectiveGalleryPanDepth}
        durationInFrames={672}
        fps={60}
        width={1920}
        height={1080}
      />
    </>
  );
};
