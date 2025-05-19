import { useEffect } from "react";
import { CustomPodcast } from "@/components/CustomPodcast";
import { TopicPodcast } from "@/components/TopicPodcast";
import { PodcastLibrary } from "@/components/PodcastLibrary";
import { Toaster } from "@/components/ui/toaster";

export default function App() {
  useEffect(() => {
    const script = document.createElement("script");
    script.src = "https://buttons.github.io/buttons.js";
    script.async = true;
    document.body.appendChild(script);

    return () => {
      document.body.removeChild(script);
    };
  }, []);

  return (
    <div className="min-h-screen w-full bg-background">
      <div className="container mx-auto py-8 px-4">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-3">OpenPod</h1>
          <p className="text-lg text-muted-foreground mb-4">
            Transform any content into engaging podcast conversations
          </p>
          <div className="flex flex-column items-center justify-center gap-4 text-sm text-muted-foreground">
            <p className="text-sm text-muted-foreground">
              Powered by{" "}
              <a
                href="https://podcastfy.ai"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline font-medium"
              >
                Podcastfy
              </a>
            </p>
            <a
              className="github-button"
              href="https://github.com/giulioco/openpod"
              data-color-scheme="no-preference: light_high_contrast; light: dark; dark: dark;"
              data-size="large"
              data-show-count="true"
              aria-label="Star giulioco/openpod on GitHub"
            >
              Star
            </a>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">
          <div className="lg:col-span-1">
            <CustomPodcast />
          </div>
          <div className="lg:col-span-1">
            <TopicPodcast />
          </div>
          <div className="lg:col-span-1">
            <PodcastLibrary />
          </div>
        </div>
      </div>
      <Toaster />
    </div>
  );
}
