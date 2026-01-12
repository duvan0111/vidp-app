'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'

// Types
interface VideoMetadata {
  video_id: string
  original_filename: string
  file_path: string
  file_size: number
  content_type: string
  status: 'uploaded' | 'processing' | 'completed' | 'failed'
  upload_time: string
  processing_time?: string
  processing_start_time?: string
  completion_time?: string
  current_stage?: string
  stages_completed?: string[]
  stages_failed?: string[]
}

interface ProcessingResult {
  video_id: string
  processing_type: string
  result: any
  created_at?: string
}

interface LanguageDetectionResult {
  detected_language?: string
  language_name?: string
  confidence?: number
  processing_time?: number
}

interface CompressionResult {
  resolution?: string
  crf_value?: number
  metadata?: {
    original_size?: number
    compressed_size?: number
    compression_ratio?: string
    duration?: number
    bitrate?: number
  }
  output_path?: string
}

interface SubtitleResult {
  model_name?: string
  language?: string
  subtitle_text?: string
}

interface AnimalDetectionResult {
  video_info?: {
    duration_seconds: number
    fps: number
    resolution: string
    total_frames: number
    processed_frames: number
  }
  detection_summary?: {
    total_detections: number
    unique_classes: number
    animals_detected: Record<string, number>
    frames_with_detections: number
  }
  output_video?: string
}

export default function VideoDetailPage() {
  const params = useParams()
  const router = useRouter()
  const videoId = params.id as string

  const [video, setVideo] = useState<VideoMetadata | null>(null)
  const [languageResult, setLanguageResult] = useState<LanguageDetectionResult | null>(null)
  const [compressionResult, setCompressionResult] = useState<CompressionResult | null>(null)
  const [subtitleResult, setSubtitleResult] = useState<SubtitleResult | null>(null)
  const [animalResult, setAnimalResult] = useState<AnimalDetectionResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch video metadata and processing results
  useEffect(() => {
    const fetchVideoData = async () => {
      try {
        setLoading(true)
        setError(null)

        // Fetch video metadata
        const videoResponse = await fetch(`http://localhost:8000/api/v1/videos/${videoId}`)
        if (!videoResponse.ok) {
          throw new Error('Vidéo non trouvée')
        }
        const videoData = await videoResponse.json()
        setVideo(videoData)

        // Fetch processing results only if video is completed
        if (videoData.status === 'completed') {
          // Language detection
          try {
            const langResponse = await fetch(`http://localhost:8000/api/v1/processing/language-detection/${videoId}`)
            if (langResponse.ok) {
              const langData = await langResponse.json()
              setLanguageResult(langData)
            }
          } catch (err) {
            console.log('Language detection result not available')
          }

          // Compression
          try {
            const compResponse = await fetch(`http://localhost:8000/api/v1/processing/compression/${videoId}`)
            if (compResponse.ok) {
              const compData = await compResponse.json()
              setCompressionResult(compData)
            }
          } catch (err) {
            console.log('Compression result not available')
          }

          // Subtitles
          try {
            const subResponse = await fetch(`http://localhost:8000/api/v1/processing/subtitles/${videoId}`)
            if (subResponse.ok) {
              const subData = await subResponse.json()
              setSubtitleResult(subData)
            }
          } catch (err) {
            console.log('Subtitle result not available')
          }

          // Animal detection
          try {
            const animalResponse = await fetch(`http://localhost:8000/api/v1/processing/animal-detection/${videoId}`)
            if (animalResponse.ok) {
              const animalData = await animalResponse.json()
              setAnimalResult(animalData.result)
            }
          } catch (err) {
            console.log('Animal detection result not available')
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Erreur lors du chargement')
      } finally {
        setLoading(false)
      }
    }

    if (videoId) {
      fetchVideoData()
      // Refresh every 3 seconds if processing
      const interval = setInterval(() => {
        if (video?.status === 'processing') {
          fetchVideoData()
        }
      }, 3000)
      return () => clearInterval(interval)
    }
  }, [videoId, video?.status])

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatDate = (dateStr: string): string => {
    return new Date(dateStr).toLocaleString('fr-FR')
  }

  // Component for Pod status card
  const PodStatusCard = ({ 
    name, 
    icon, 
    color, 
    children 
  }: { 
    name: string
    icon: string
    color: string
    children: React.ReactNode 
  }) => (
    <div 
      className="bg-gray-800/70 p-4 rounded-lg border-l-4 mb-3 hover:bg-gray-800 transition-colors"
      style={{ borderLeftColor: color }}
    >
      <div className="flex items-center gap-3 mb-2">
        <span className="text-2xl">{icon}</span>
        <div>
          <div className="text-xs text-gray-400 uppercase font-bold">{name}</div>
          {children}
        </div>
      </div>
    </div>
  )

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Chargement...</p>
        </div>
      </div>
    )
  }

  if (error || !video) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">❌</div>
          <h2 className="text-2xl font-bold mb-2">Erreur</h2>
          <p className="text-gray-400 mb-4">{error || 'Vidéo non trouvée'}</p>
          <button
            onClick={() => router.push('/')}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors"
          >
            ← Retour à l'accueil
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => router.push('/')}
                className="text-gray-400 hover:text-white transition-colors"
              >
                ← Retour
              </button>
              <div className="flex items-center gap-2">
                <span className="text-red-500 text-2xl">▶</span>
                <h1 className="text-xl font-bold">
                  VidP <span className="text-gray-400 font-normal">Studio</span>
                </h1>
              </div>
            </div>
            <div>
              {video.status === 'completed' && (
                <span className="bg-green-600 text-white px-3 py-1 rounded-full text-xs font-bold">
                  ✓ TRAITEMENT TERMINÉ
                </span>
              )}
              {video.status === 'processing' && (
                <span className="bg-yellow-500 text-black px-3 py-1 rounded-full text-xs font-bold animate-pulse">
                  ⚙️ EN COURS
                </span>
              )}
              {video.status === 'failed' && (
                <span className="bg-red-600 text-white px-3 py-1 rounded-full text-xs font-bold">
                  ✗ ÉCHOUÉ
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Left Column - Video Player */}
          <div className="flex-1 lg:w-3/5">
            <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700">
              {/* Video Player */}
              <div className="w-full aspect-video bg-black rounded-lg overflow-hidden shadow-2xl mb-6">
                {video.status === 'completed' ? (
                  <video
                    controls
                    autoPlay
                    className="w-full h-full"
                    src={`http://localhost:8000/api/v1/videos/stream/${videoId}`}
                  >
                    Votre navigateur ne supporte pas la lecture vidéo.
                  </video>
                ) : video.status === 'processing' ? (
                  <div className="w-full h-full flex flex-col items-center justify-center text-gray-400">
                    <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-red-500 mb-4"></div>
                    <h2 className="text-xl font-semibold mb-2">Traitement Cloud en cours...</h2>
                    <p className="text-sm">Pipeline Kubernetes actif</p>
                  </div>
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-red-400">
                    <div className="text-center">
                      <div className="text-6xl mb-4">❌</div>
                      <p>Traitement échoué</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Video Info */}
              <div>
                <h2 className="text-2xl font-bold mb-2">{video.original_filename}</h2>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-400">Taille:</span>
                    <span className="ml-2 text-white font-medium">{formatFileSize(video.file_size)}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Format:</span>
                    <span className="ml-2 text-white font-medium">{video.content_type}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Upload:</span>
                    <span className="ml-2 text-white font-medium">{formatDate(video.upload_time)}</span>
                  </div>
                  {video.completion_time && (
                    <div>
                      <span className="text-gray-400">Traité le:</span>
                      <span className="ml-2 text-white font-medium">{formatDate(video.completion_time)}</span>
                    </div>
                  )}
                  <div className="col-span-2">
                    <span className="text-gray-400">ID:</span>
                    <span className="ml-2 text-blue-400 font-mono text-xs">{video.video_id}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column - Pod Reports */}
          <div className="lg:w-2/5">
            <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700">
              <div className="flex items-center gap-2 mb-6 border-b border-gray-700 pb-4">
                <h3 className="text-xl font-bold flex items-center gap-2">
                  📡 Rapport des Pods
                </h3>
                <span className="text-xs bg-gray-700 px-2 py-1 rounded">KUBERNETES</span>
              </div>

              {video.status === 'completed' ? (
                <div className="space-y-3">
                  {/* Pod 1: Language Detection */}
                  <PodStatusCard name="Language Detection Pod" icon="🗣" color="#3498db">
                    {languageResult ? (
                      <div className="text-sm">
                        <p className="text-white font-semibold">
                          {languageResult.language_name || languageResult.detected_language || 'Non détecté'}
                        </p>
                        {languageResult.confidence && (
                          <p className="text-gray-400 text-xs">
                            Confiance: {(languageResult.confidence * 100).toFixed(1)}%
                          </p>
                        )}
                      </div>
                    ) : (
                      <p className="text-gray-500 text-sm">Résultat non disponible</p>
                    )}
                  </PodStatusCard>

                  {/* Pod 2: Compression/Downscale */}
                  <PodStatusCard name="Downscale Pod" icon="📉" color="#2ecc71">
                    {compressionResult ? (
                      <div className="text-sm">
                        <p className="text-white font-semibold">
                          {compressionResult.resolution || 'Optimisé'}
                        </p>
                        {compressionResult.metadata && (
                          <div className="text-gray-400 text-xs mt-1">
                            {compressionResult.metadata.compression_ratio && (
                              <p>Ratio: {compressionResult.metadata.compression_ratio}</p>
                            )}
                            {compressionResult.metadata.compressed_size && (
                              <p>Taille: {formatFileSize(compressionResult.metadata.compressed_size)}</p>
                            )}
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-gray-500 text-sm">Résultat non disponible</p>
                    )}
                  </PodStatusCard>

                  {/* Pod 3: Subtitle Generation */}
                  <PodStatusCard name="Subtitle Pod" icon="📝" color="#9b59b6">
                    {subtitleResult ? (
                      <div className="text-sm">
                        <p className="text-white font-semibold">
                          Sous-titres générés (.srt)
                        </p>
                        <p className="text-gray-400 text-xs">
                          Modèle: {subtitleResult.model_name || 'Whisper'} | Langue: {subtitleResult.language || 'Auto'}
                        </p>
                        {subtitleResult.subtitle_text && (
                          <div className="mt-2 bg-gray-900/50 p-2 rounded text-xs text-gray-300 max-h-24 overflow-y-auto">
                            {subtitleResult.subtitle_text.substring(0, 200)}...
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-gray-500 text-sm">Résultat non disponible</p>
                    )}
                  </PodStatusCard>

                  {/* Pod 4: Animal Detection */}
                  <div className="bg-gray-800/70 p-4 rounded-lg border-l-4 border-orange-500">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-2xl">🐾</span>
                      <div className="flex-1">
                        <div className="text-xs text-gray-400 uppercase font-bold">Animal Detect Pod</div>
                        {animalResult ? (
                          <div className="mt-2">
                            {animalResult.detection_summary && animalResult.detection_summary.animals_detected && 
                             Object.keys(animalResult.detection_summary.animals_detected).length > 0 ? (
                              <div>
                                <p className="text-sm text-gray-300 mb-2">
                                  {animalResult.detection_summary.total_detections} détection(s) - {animalResult.detection_summary.unique_classes} classe(s)
                                </p>
                                <div className="flex flex-wrap gap-2">
                                  {Object.entries(animalResult.detection_summary.animals_detected).map(([animal, count]) => (
                                    <span 
                                      key={animal} 
                                      className="bg-orange-500 text-white text-xs px-2 py-1 rounded-full font-semibold"
                                    >
                                      {animal}: {count}
                                    </span>
                                  ))}
                                </div>
                                {animalResult.video_info && (
                                  <p className="text-xs text-gray-500 mt-2">
                                    {animalResult.video_info.processed_frames}/{animalResult.video_info.total_frames} frames analysées
                                  </p>
                                )}
                              </div>
                            ) : (
                              <p className="text-gray-500 text-sm">Aucun animal détecté</p>
                            )}
                          </div>
                        ) : (
                          <p className="text-gray-500 text-sm">Résultat non disponible</p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ) : video.status === 'processing' ? (
                <div className="text-center py-8">
                  <div className="animate-pulse space-y-3">
                    <div className="h-16 bg-gray-700/50 rounded"></div>
                    <div className="h-16 bg-gray-700/50 rounded"></div>
                    <div className="h-16 bg-gray-700/50 rounded"></div>
                    <div className="h-16 bg-gray-700/50 rounded"></div>
                  </div>
                  <p className="text-gray-400 italic mt-4">
                    Les Pods analysent le flux vidéo...
                  </p>
                  {video.current_stage && (
                    <p className="text-yellow-400 text-sm mt-2">
                      Étape actuelle: {video.current_stage}
                    </p>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-red-400">
                  <div className="text-6xl mb-4">⚠️</div>
                  <p>Le traitement a échoué</p>
                  {video.stages_failed && video.stages_failed.length > 0 && (
                    <p className="text-sm text-gray-400 mt-2">
                      Étape(s) échouée(s): {video.stages_failed.join(', ')}
                    </p>
                  )}
                </div>
              )}

              {/* Processing Timeline */}
              {video.stages_completed && video.stages_completed.length > 0 && (
                <div className="mt-6 pt-6 border-t border-gray-700">
                  <h4 className="text-sm font-semibold text-gray-400 mb-3">PROGRESSION DU PIPELINE</h4>
                  <div className="space-y-2">
                    {['language_detection', 'compression', 'subtitle_generation', 'animal_detection'].map((stage) => {
                      const isCompleted = video.stages_completed?.includes(stage)
                      const isFailed = video.stages_failed?.includes(stage)
                      const isCurrent = video.current_stage === stage
                      
                      const stageLabels: Record<string, string> = {
                        language_detection: '🌍 Détection langue',
                        compression: '📐 Compression',
                        subtitle_generation: '📝 Sous-titres',
                        animal_detection: '🐾 Détection animaux'
                      }
                      
                      return (
                        <div 
                          key={stage}
                          className={`flex items-center gap-2 text-sm ${
                            isCompleted ? 'text-green-400' :
                            isFailed ? 'text-red-400' :
                            isCurrent ? 'text-yellow-400' :
                            'text-gray-600'
                          }`}
                        >
                          <span>
                            {isCompleted ? '✓' : isFailed ? '✗' : isCurrent ? '⏳' : '○'}
                          </span>
                          <span>{stageLabels[stage]}</span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="text-center py-8 border-t border-gray-700 mt-12">
        <p className="text-gray-400">
          INF5141 Cloud Computing - Projet VidP | Réalisé par HN-DS-CIN 5 © 2025
        </p>
      </footer>
    </div>
  )
}
