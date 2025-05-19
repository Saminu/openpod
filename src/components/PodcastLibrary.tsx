import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Play, Pause, Download, Clock, Trash2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

interface PodcastFile {
  id: string;
  name: string;
  url: string;
  date: string;
  duration?: string;
}

export function PodcastLibrary() {
  const [podcasts, setPodcasts] = useState<PodcastFile[]>([]);
  const [currentlyPlaying, setCurrentlyPlaying] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();

  // Load podcasts from localStorage on component mount
  useEffect(() => {
    const savedPodcasts = localStorage.getItem("saved_podcasts");
    if (savedPodcasts) {
      setPodcasts(JSON.parse(savedPodcasts));
    }
    setIsLoading(false);
  }, []);

  // Save a new podcast to the library
  const addPodcast = (podcast: PodcastFile) => {
    const updatedPodcasts = [...podcasts, podcast];
    setPodcasts(updatedPodcasts);
    localStorage.setItem("saved_podcasts", JSON.stringify(updatedPodcasts));
    toast({
      title: "Podcast Saved",
      description: "The podcast has been added to your library",
    });
  };

  // Remove a podcast from the library
  const removePodcast = (id: string) => {
    const updatedPodcasts = podcasts.filter((podcast) => podcast.id !== id);
    setPodcasts(updatedPodcasts);
    localStorage.setItem("saved_podcasts", JSON.stringify(updatedPodcasts));
    
    // If the deleted podcast was playing, stop it
    if (currentlyPlaying === id) {
      setCurrentlyPlaying(null);
    }
    
    toast({
      title: "Podcast Removed",
      description: "The podcast has been removed from your library",
    });
  };

  // Toggle play/pause for a podcast
  const togglePlayPause = (id: string) => {
    if (currentlyPlaying === id) {
      setCurrentlyPlaying(null);
    } else {
      setCurrentlyPlaying(id);
    }
  };

  // Format date for display
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString();
  };

  return (
    <Card className="p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Your Podcasts</h2>
      </div>

      {isLoading ? (
        <div className="py-8 text-center text-muted-foreground">
          Loading your podcasts...
        </div>
      ) : podcasts.length === 0 ? (
        <div className="py-8 text-center text-muted-foreground">
          <p>No podcasts in your library yet.</p>
          <p className="text-sm mt-2">
            Generate a podcast and it will appear here.
          </p>
        </div>
      ) : (
        <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
          {podcasts.map((podcast) => (
            <div
              key={podcast.id}
              className="bg-secondary/30 rounded-lg p-3 hover:bg-secondary/50 transition-colors"
            >
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-medium text-sm line-clamp-1">{podcast.name || "Untitled Podcast"}</h3>
                <div className="flex items-center space-x-1">
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7"
                          onClick={() => window.open(podcast.url)}
                        >
                          <Download className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Download</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                  
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-destructive/70 hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Remove Podcast</AlertDialogTitle>
                        <AlertDialogDescription>
                          Are you sure you want to remove this podcast from your library?
                          This action cannot be undone.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction onClick={() => removePodcast(podcast.id)}>
                          Remove
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center text-xs text-muted-foreground space-x-2">
                  <span>{formatDate(podcast.date)}</span>
                  {podcast.duration && (
                    <>
                      <span>•</span>
                      <span className="flex items-center">
                        <Clock className="h-3 w-3 mr-1" />
                        {podcast.duration}
                      </span>
                    </>
                  )}
                </div>
                
                <Button
                  variant="secondary"
                  size="sm"
                  className="h-8 px-2"
                  onClick={() => togglePlayPause(podcast.id)}
                >
                  {currentlyPlaying === podcast.id ? (
                    <>
                      <Pause className="h-4 w-4 mr-1" />
                      Pause
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-1" />
                      Play
                    </>
                  )}
                </Button>
              </div>
              
              {currentlyPlaying === podcast.id && (
                <div className="mt-3">
                  <audio
                    controls
                    autoPlay
                    className="w-full h-8"
                    onEnded={() => setCurrentlyPlaying(null)}
                  >
                    <source src={podcast.url} type="audio/mpeg" />
                    Your browser does not support the audio element.
                  </audio>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

// Function to be called from other components to add a podcast to the library
export function addPodcastToLibrary(url: string, name: string = "Generated Podcast") {
  const savedPodcasts = localStorage.getItem("saved_podcasts");
  let podcasts: PodcastFile[] = savedPodcasts ? JSON.parse(savedPodcasts) : [];
  
  const newPodcast: PodcastFile = {
    id: Date.now().toString(),
    name,
    url,
    date: new Date().toISOString(),
  };
  
  podcasts = [...podcasts, newPodcast];
  localStorage.setItem("saved_podcasts", JSON.stringify(podcasts));
  
  return newPodcast;
}
