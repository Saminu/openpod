import { CustomPodcast } from "@/components/CustomPodcast";
import { TopicPodcast } from "@/components/TopicPodcast";
import { PodcastLibrary } from "@/components/PodcastLibrary";
import { Toaster } from "@/components/ui/toaster";

export default function App() {

  return (
    <div className="h-screen w-full bg-background flex flex-col overflow-hidden">
      <div className="flex items-center justify-center bg-card py-4 px-6 border-b border-border shadow-md">
        <div className="flex items-center">
          <img src="/echosphere-logo-modern.svg" alt="EchoSphere Logo" className="h-10 w-10 mr-3" />
          <h1 className="text-2xl font-bold bg-gradient-to-r from-[#0DFFD8] to-[#00B3A0] text-transparent bg-clip-text">Spark Audio Notebook</h1>
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        <div className="h-full grid grid-cols-1 lg:grid-cols-3 gap-4 p-4 overflow-auto">
          <div className="lg:col-span-1 overflow-auto">
            <CustomPodcast />
          </div>
          <div className="lg:col-span-1 overflow-auto">
            <TopicPodcast />
          </div>
          <div className="lg:col-span-1 overflow-auto">
            <PodcastLibrary />
          </div>
        </div>
      </div>
      <Toaster />
    </div>
  );
}
