import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Play, Download, Save, Globe } from "lucide-react";
import { io } from "socket.io-client";
import { Card } from "@/components/ui/card";
import { addPodcastToLibrary } from "@/components/PodcastLibrary";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export function TopicPodcast() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");
  const [audioUrl, setAudioUrl] = useState("");
  const [transcript, setTranscript] = useState("");
  const [topic, setTopic] = useState("");
  const [language, setLanguage] = useState("English");
  const { toast } = useToast();

  const generateTopicPodcast = async () => {
    if (!topic.trim()) {
      toast({
        title: "Missing Topic",
        description: "Please enter a topic you'd like to learn about",
        variant: "destructive",
      });
      return;
    }

    // API keys are now loaded from .env file on the server

    setIsGenerating(true);
    setProgress(0);
    setStatusMessage("Connecting to server...");
    setAudioUrl("");
    setTranscript("");

    try {
      const socket = io("http://localhost:8082", {
        path: "/socket.io",
        reconnection: true,
        timeout: 20000, // Increase timeout
        reconnectionAttempts: 3,
        transports: ['websocket', 'polling']
      });

      // Set a timeout in case the connection hangs
      const connectionTimeout = setTimeout(() => {
        if (socket.connected === false) {
          console.error("Connection timeout");
          toast({
            title: "Connection Timeout",
            description: "Could not connect to the server. Please try again.",
            variant: "destructive",
          });
          socket.disconnect();
          setIsGenerating(false);
        }
      }, 15000);

      socket.on("connect", () => {
        console.log("Socket connected successfully");
        clearTimeout(connectionTimeout);
        setStatusMessage("Connected to server");
        setProgress(10);

        const payload = {
          topics: topic,
          output_language: language,
        };

        console.log("Sending request:", payload);
        socket.emit("generate_news_podcast", payload);
      });

      socket.on("connect_error", (error) => {
        console.error("Connection error:", error);
        clearTimeout(connectionTimeout);
        toast({
          title: "Connection Error",
          description: "Could not connect to the server. Please check if the server is running.",
          variant: "destructive",
        });
        setIsGenerating(false);
      });

      socket.on("status", (message: string) => {
        console.log("Status update:", message);
        setStatusMessage(message);
      });

      socket.on("progress", (data: { progress: number; message: string }) => {
        console.log("Progress update:", data);
        setProgress(data.progress);
        setStatusMessage(data.message);
      });

      socket.on(
        "complete",
        (data: { audioUrl: string; transcript: string }) => {
          console.log("Podcast generation complete:", data);
          setAudioUrl(data.audioUrl);
          setTranscript(data.transcript);
          socket.disconnect();
          setIsGenerating(false);

          toast({
            title: "Success",
            description: "Podcast generated successfully!",
          });
        }
      );

      socket.on("error", (error: { message: string }) => {
        console.error("Socket error:", error);
        toast({
          title: "Error",
          description: error.message || "Failed to generate podcast",
          variant: "destructive",
        });
        socket.disconnect();
        setIsGenerating(false);
      });

      socket.on("disconnect", () => {
        console.log("Socket disconnected");
        clearTimeout(connectionTimeout);
        if (isGenerating) {
          toast({
            title: "Connection Lost",
            description: "The connection to the server was lost",
            variant: "destructive",
          });
          setIsGenerating(false);
        }
      });
    } catch (error: any) {
      console.error("Error in generateTopicPodcast:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to generate podcast",
        variant: "destructive",
      });
      setIsGenerating(false);
    }
  };

  return (
    <Card className="p-6 space-y-6">
      <div className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold mb-2 bg-gradient-to-r from-[#0DFFD8] to-[#00B3A0] text-transparent bg-clip-text">Topic Explorer</h2>
          <p className="text-sm text-muted-foreground mb-4">
            Enter any topic and we'll research it, synthesize the information,
            and create an engaging podcast discussion about it. Perfect for
            learning about new subjects or getting a comprehensive overview of
            any topic.
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="topic">Topic</Label>
          <Input
            id="topic"
            placeholder="e.g., Quantum Computing, Climate Change, History of Jazz"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
          />
          <p className="text-sm text-muted-foreground">
            Be as specific or broad as you'd like. We'll research and create an
            informative discussion about it.
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="language" className="flex items-center gap-2">
            <Globe className="h-4 w-4" />
            Language
          </Label>
          <Select
            value={language}
            onValueChange={setLanguage}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select language" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="English">English</SelectItem>
              <SelectItem value="Spanish">Spanish (Español)</SelectItem>
              <SelectItem value="French">French (Français)</SelectItem>
              <SelectItem value="German">German (Deutsch)</SelectItem>
              <SelectItem value="Italian">Italian (Italiano)</SelectItem>
              <SelectItem value="Portuguese">Portuguese (Português)</SelectItem>
              <SelectItem value="Dutch">Dutch (Nederlands)</SelectItem>
              <SelectItem value="Russian">Russian (Русский)</SelectItem>
              <SelectItem value="Japanese">Japanese (日本語)</SelectItem>
              <SelectItem value="Chinese">Chinese (中文)</SelectItem>
              <SelectItem value="Korean">Korean (한국어)</SelectItem>
              <SelectItem value="Arabic">Arabic (العربية)</SelectItem>
              <SelectItem value="Hindi">Hindi (हिन्दी)</SelectItem>
            </SelectContent>
          </Select>
          <p className="text-sm text-muted-foreground">
            Select the language for your podcast. The AI will generate content in this language.
          </p>
        </div>
      </div>

      {isGenerating && (
        <div className="space-y-2">
          <Progress value={progress} className="w-full" />
          <p className="text-sm text-center text-muted-foreground">
            {statusMessage || `Generating podcast... ${progress}%`}
          </p>
        </div>
      )}

      {audioUrl && (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Generated Topic Podcast</Label>
            <audio controls className="w-full">
              <source src={audioUrl} type="audio/mpeg" />
              Your browser does not support the audio element.
            </audio>
          </div>

          <div className="flex space-x-2">
            <Button
              className="flex-1"
              onClick={() => window.open(audioUrl)}
              variant="secondary"
            >
              <Download className="mr-2 h-4 w-4" />
              Download
            </Button>
            <Button
              className="flex-1"
              onClick={() => {
                const podcastName = `Topic Podcast: ${topic}`;
                addPodcastToLibrary(audioUrl, podcastName);
                toast({
                  title: "Saved to Library",
                  description: "Podcast has been added to your library",
                });
              }}
              variant="default"
            >
              <Save className="w-4 h-4 mr-2" />
              Save to Library
            </Button>
          </div>

          {transcript && (
            <Accordion type="single" collapsible>
              <AccordionItem value="transcript">
                <AccordionTrigger>View Transcript</AccordionTrigger>
                <AccordionContent>
                  <div className="bg-secondary/50 p-4 rounded-md">
                    <pre className="whitespace-pre-wrap text-sm">
                      {transcript}
                    </pre>
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          )}
        </div>
      )}

      <Button
        onClick={generateTopicPodcast}
        className="w-full"
        disabled={isGenerating}
      >
        {isGenerating ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Researching and Generating Podcast
          </>
        ) : (
          <>
            <Play className="mr-2 h-4 w-4" />
            Generate Topic Podcast
          </>
        )}
      </Button>
    </Card>
  );
}
