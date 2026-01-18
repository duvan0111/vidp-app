'use client'

import { useState, useRef, DragEvent, useEffect } from 'react'

// Constantes d'API
const API_LIST_URL = 'http://localhost:8000/api/v1/videos/'
const API_GLOBAL_PROCESSING_URL = 'http://localhost:8000/api/v1/processing/process-video'
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const API_ANIMAL_DETECTION_URL = 'http://localhost:8000/api/v1/processing/animal-detection'
// Nouvelle constante pour le streaming via main-app
const API_STREAMING_URL = 'http://localhost:8000/api/v1/videos/stream/'

// Types d'upload
type UploadState = 'IDLE' | 'SELECTED' | 'UPLOADING' | 'SUCCESS' | 'ERROR'
type VideoStatus = 'uploaded' | 'processing' | 'completed' | 'failed'
type ProcessingStageStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'skipped'

interface ApiResponse {
  video_id?: string
  message?: string
  detail?: string
}

interface ProcessingStageResult {
  stage: string
  status: ProcessingStageStatus
  result?: {
    // Champs communs pour étapes sautées
    skipped?: boolean
    reason?: string
    // Détection de langue
    detected_language?: string
    language_name?: string
    confidence?: number
    // Compression
    resolution?: string
    output_path?: string
    // Sous-titres
    model_name?: string
    language?: string
    subtitle_text?: string
    subtitle_text_preview?: string
    text_length?: number
    srt_url?: string
    srt_content?: string
    // Animal detection results
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
    // Aggregation results
    job_id?: string
    aggregated_video_id?: string
    streaming_url?: string
    has_subtitles?: boolean
    no_audio?: boolean
    metadata?: {
      original_filename?: string
      final_filename?: string
      resolution?: string
      duration?: number
      file_size?: number
    }
  }
  error_message?: string
  duration?: number
}

interface GlobalProcessingResponse {
  video_id: string
  overall_status: string
  message: string
  total_duration?: number
  success_count: number
  failure_count: number
  skipped_count: number
  language_detection?: ProcessingStageResult
  compression?: ProcessingStageResult
  subtitle_generation?: ProcessingStageResult
  animal_detection?: ProcessingStageResult
  aggregation?: ProcessingStageResult
  final_streaming_url?: string
}

interface VideoMetadata {
  video_id: string
  original_filename: string
  file_path: string
  file_size: number
  content_type: string
  status: VideoStatus
  upload_time: string
  processing_time?: string
  processing_start_time?: string
  completion_time?: string
  // Progression du traitement
  current_stage?: string
  stages_completed?: string[]
  stages_failed?: string[]
  // ID de la vidéo agrégée (pour le streaming via vidp-cloud-visualisation-app)
  aggregated_video_id?: string
}

// Composant VideoUploader avec traitement global OBLIGATOIRE
function VideoUploader({ onUploadSuccess }: { onUploadSuccess: () => void }) {
  const [uploadState, setUploadState] = useState<UploadState>('IDLE')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadProgress, setUploadProgress] = useState<number>(0)
  const [apiResponse, setApiResponse] = useState<ApiResponse | null>(null)
  const [globalResponse, setGlobalResponse] = useState<GlobalProcessingResponse | null>(null)
  const [errorMessage, setErrorMessage] = useState<string>('')
  const [notification, setNotification] = useState<{message: string, type: 'success' | 'info' | 'error'} | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [showAdvancedOptions, setShowAdvancedOptions] = useState<boolean>(false)

  // Paramètres configurables du pipeline
  const [pipelineOptions, setPipelineOptions] = useState({
    languageDetectionDuration: 30,
    targetResolution: '360p',
    crf: 23,
    subtitleModel: 'tiny',
    subtitleLanguage: 'auto',
    // Options détection d'animaux - TOUJOURS ACTIVÉ par défaut
    enableAnimalDetection: true,
    animalConfidenceThreshold: 0.5
  })

  // Formats vidéo acceptés
  const acceptedFormats = ['video/mp4', 'video/avi', 'video/mov', 'video/quicktime', 'video/x-msvideo']
  const maxFileSize = 500 * 1024 * 1024 // 500 MB

  // Validation du fichier
  const validateFile = (file: File): string | null => {
    if (!acceptedFormats.includes(file.type)) {
      return 'Format de fichier non supporté. Veuillez sélectionner un fichier MP4, AVI ou MOV.'
    }
    if (file.size > maxFileSize) {
      return 'La taille du fichier dépasse 500 MB. Veuillez sélectionner un fichier plus petit.'
    }
    return null
  }

  // Gestionnaire de sélection de fichier
  const handleFileSelect = (file: File) => {
    const validationError = validateFile(file)
    if (validationError) {
      setErrorMessage(validationError)
      setUploadState('ERROR')
      return
    }

    setSelectedFile(file)
    setUploadState('SELECTED')
    setErrorMessage('')
    setApiResponse(null)
  }

  // Gestionnaire d'événement input
  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      handleFileSelect(file)
    }
  }

  // Gestionnaire drag & drop
  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    
    const files = e.dataTransfer.files
    if (files.length > 0) {
      handleFileSelect(files[0])
    }
  }

  // Gestionnaire d'upload - TRAITEMENT OBLIGATOIRE
  const handleUpload = async () => {
    if (!selectedFile) return

    setUploadState('UPLOADING')
    setUploadProgress(0)
    setErrorMessage('')
    setGlobalResponse(null)

    const formData = new FormData()
    formData.append('video_file', selectedFile)
    
    // Ajouter les paramètres configurables du pipeline
    formData.append('language_detection_duration', String(pipelineOptions.languageDetectionDuration))
    formData.append('target_resolution', pipelineOptions.targetResolution)
    formData.append('crf', String(pipelineOptions.crf))
    formData.append('subtitle_model', pipelineOptions.subtitleModel)
    formData.append('subtitle_language', pipelineOptions.subtitleLanguage)
    // Paramètres détection d'animaux
    formData.append('enable_animal_detection', String(pipelineOptions.enableAnimalDetection))
    formData.append('animal_confidence_threshold', String(pipelineOptions.animalConfidenceThreshold))

    try {
      const xhr = new XMLHttpRequest()
      
      // Timeout de 30 minutes pour les traitements longs (vidéos volumineuses)
      // Ce timeout couvre l'ensemble du traitement (upload + 4 étapes de processing)
      xhr.timeout = 1800000 // 30 minutes en millisecondes

      // Gestionnaire de progression
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          const percentComplete = (e.loaded / e.total) * 100
          setUploadProgress(percentComplete)
          
          // Dès que l'upload est terminé (100%), on reset pour permettre un nouvel upload
          // Le traitement continue en arrière-plan côté serveur
          if (percentComplete >= 100) {
            setTimeout(() => {
              const savedFileName = selectedFile?.name || 'Vidéo'
              setSelectedFile(null)
              setUploadState('IDLE')
              setUploadProgress(0)
              if (fileInputRef.current) {
                fileInputRef.current.value = ''
              }
              // Afficher notification
              setNotification({
                message: `🚀 "${savedFileName}" envoyée en traitement ! Suivez la progression dans "Traitement en cours"`,
                type: 'success'
              })
              // Auto-hide après 5 secondes
              setTimeout(() => setNotification(null), 5000)
              // Rafraîchir la liste pour voir la vidéo en cours de traitement
              onUploadSuccess()
            }, 800)
          }
        }
      }

      // Gestionnaire de réponse
      xhr.onload = () => {
        // La réponse arrive après le traitement complet
        // Le formulaire est déjà reset, on rafraîchit juste la liste
        onUploadSuccess()
      }

      // Gestionnaire d'erreur
      xhr.onerror = () => {
        setErrorMessage('Erreur réseau lors de l\'upload')
        setUploadState('ERROR')
      }

      // Gestionnaire de timeout
      xhr.ontimeout = () => {
        setErrorMessage('Le traitement a pris trop de temps (> 30 minutes). Vérifiez la vidéo dans la liste.')
        setUploadState('ERROR')
        // Rafraîchir la liste quand même car le traitement peut avoir réussi côté serveur
        onUploadSuccess()
      }

      // Envoi de la requête
      xhr.open('POST', API_GLOBAL_PROCESSING_URL)
      xhr.send(formData)

    } catch (error) {
      setErrorMessage('Erreur lors de l\'upload: ' + (error instanceof Error ? error.message : 'Erreur inconnue'))
      setUploadState('ERROR')
    }
  }

  // Gestionnaire de reset
  const handleReset = () => {
    setSelectedFile(null)
    setUploadState('IDLE')
    setUploadProgress(0)
    setApiResponse(null)
    setGlobalResponse(null)
    setErrorMessage('')
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  // Formatage de la taille du fichier
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  // Formatage de la durée
  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`
    const mins = Math.floor(seconds / 60)
    const secs = (seconds % 60).toFixed(0)
    return `${mins}m ${secs}s`
  }

  // Obtenir l'icône et la couleur pour un statut d'étape
  const getStageStatus = (status: ProcessingStageStatus) => {
    const statuses = {
      pending: { icon: '⏳', color: 'text-gray-400', bg: 'bg-gray-600' },
      processing: { icon: '🔄', color: 'text-blue-400', bg: 'bg-blue-600' },
      completed: { icon: '✅', color: 'text-green-400', bg: 'bg-green-600' },
      failed: { icon: '❌', color: 'text-red-400', bg: 'bg-red-600' },
      skipped: { icon: '⏭️', color: 'text-yellow-400', bg: 'bg-yellow-600' }
    }
    return statuses[status] || statuses.pending
  }

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      {/* Notification Toast */}
      {notification && (
        <div className={`fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-md animate-pulse ${
          notification.type === 'success' ? 'bg-green-600 text-white' :
          notification.type === 'error' ? 'bg-red-600 text-white' :
          'bg-blue-600 text-white'
        }`}>
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-medium">{notification.message}</p>
            <button 
              onClick={() => setNotification(null)}
              className="text-white/80 hover:text-white"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Bandeau d'information - Pipeline obligatoire */}
      {/* <div className="bg-gradient-to-r from-blue-900/50 to-purple-900/50 border border-blue-500/30 rounded-lg p-4">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🎬</span>
          <div>
            <h3 className="text-lg font-semibold text-white">Pipeline de traitement automatique</h3>
            <p className="text-sm text-gray-300">
              Chaque vidéo uploadée passe automatiquement par : 
              <span className="text-blue-400 font-medium"> 🌍 Détection langue</span> →
              <span className="text-green-400 font-medium"> 📐 Compression</span> →
              <span className="text-purple-400 font-medium"> 📝 Sous-titres</span>
            </p>
          </div>
        </div>
      </div> */}

      {/* Panneau de configuration du pipeline */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-lg overflow-hidden">
        <button
          onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
          className="w-full p-4 flex items-center justify-between hover:bg-gray-700/30 transition-colors"
        >
          <div className="flex items-center gap-3">
            <span className="text-xl">⚙️</span>
            <span className="font-medium text-white">Paramètres du pipeline</span>
            <span className="text-xs text-gray-500 bg-gray-700 px-2 py-1 rounded">Optionnel</span>
          </div>
          <span className="text-gray-400">{showAdvancedOptions ? '🔼' : '🔽'}</span>
        </button>
        
        {showAdvancedOptions && (
          <div className="p-4 pt-0 border-t border-gray-700">
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
              {/* Détection de langue */}
              <div className="p-4 rounded-lg border border-blue-500/30 bg-blue-900/10">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-xl">🌍</span>
                  <h4 className="font-medium text-white">Détection langue</h4>
                </div>
                <div>
                  <label className="text-xs text-gray-400">Durée d&apos;analyse (secondes)</label>
                  <input
                    type="number"
                    value={pipelineOptions.languageDetectionDuration}
                    onChange={(e) => setPipelineOptions({...pipelineOptions, languageDetectionDuration: parseInt(e.target.value) || 30})}
                    className="w-full mt-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white text-sm focus:border-blue-500 focus:outline-none"
                    min="10"
                    max="120"
                  />
                  <p className="text-xs text-gray-500 mt-1">10-120s recommandé</p>
                </div>
              </div>

              {/* Compression */}
              <div className="p-4 rounded-lg border border-green-500/30 bg-green-900/10">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-xl">📐</span>
                  <h4 className="font-medium text-white">Compression</h4>
                </div>
                <div className="space-y-3">
                  <div>
                    <label className="text-xs text-gray-400">Résolution cible</label>
                    <select
                      value={pipelineOptions.targetResolution}
                      onChange={(e) => setPipelineOptions({...pipelineOptions, targetResolution: e.target.value})}
                      className="w-full mt-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white text-sm focus:border-green-500 focus:outline-none"
                    >
                      <option value="240p">240p (très basse)</option>
                      <option value="360p">360p (basse)</option>
                      <option value="480p">480p (SD)</option>
                      <option value="720p">720p (HD)</option>
                      <option value="1080p">1080p (Full HD)</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">Qualité CRF: {pipelineOptions.crf}</label>
                    <input
                      type="range"
                      value={pipelineOptions.crf}
                      onChange={(e) => setPipelineOptions({...pipelineOptions, crf: parseInt(e.target.value)})}
                      className="w-full mt-1"
                      min="18"
                      max="28"
                    />
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>Haute qualité</span>
                      <span>Petite taille</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Sous-titres */}
              <div className="p-4 rounded-lg border border-purple-500/30 bg-purple-900/10">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-xl">📝</span>
                  <h4 className="font-medium text-white">Sous-titres</h4>
                </div>
                <div className="space-y-3">
                  <div>
                    <label className="text-xs text-gray-400">Modèle Whisper</label>
                    <select
                      value={pipelineOptions.subtitleModel}
                      onChange={(e) => setPipelineOptions({...pipelineOptions, subtitleModel: e.target.value})}
                      className="w-full mt-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white text-sm focus:border-purple-500 focus:outline-none"
                    >
                      <option value="tiny">Tiny (rapide, moins précis)</option>
                      <option value="base">Base</option>
                      <option value="small">Small</option>
                      <option value="medium">Medium</option>
                      <option value="large">Large (lent, très précis)</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">Langue</label>
                    <select
                      value={pipelineOptions.subtitleLanguage}
                      onChange={(e) => setPipelineOptions({...pipelineOptions, subtitleLanguage: e.target.value})}
                      className="w-full mt-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white text-sm focus:border-purple-500 focus:outline-none"
                    >
                      <option value="auto">Auto (utilise la détection)</option>
                      <option value="fr">Français</option>
                      <option value="en">English</option>
                      <option value="es">Español</option>
                      <option value="de">Deutsch</option>
                      <option value="it">Italiano</option>
                      <option value="pt">Português</option>
                      <option value="ar">العربية</option>
                      <option value="zh">中文</option>
                      <option value="ja">日本語</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Détection d'animaux */}
              <div className="p-4 rounded-lg border border-orange-500/50 bg-orange-900/20">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-xl">🐾</span>
                  <h4 className="font-medium text-white">Détection animaux</h4>
                  <span className="text-xs text-orange-400 bg-orange-900/50 px-2 py-1 rounded">Activé</span>
                </div>
                <div className="space-y-3">
                  <div>
                    <label className="text-xs text-gray-400">Confiance: {(pipelineOptions.animalConfidenceThreshold * 100).toFixed(0)}%</label>
                    <input
                      type="range"
                      value={pipelineOptions.animalConfidenceThreshold * 100}
                      onChange={(e) => setPipelineOptions({...pipelineOptions, animalConfidenceThreshold: parseInt(e.target.value) / 100})}
                      className="w-full mt-1"
                      min="10"
                      max="90"
                    />
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>Plus de détections</span>
                      <span>Plus précis</span>
                    </div>
                    <p className="text-xs text-orange-400 mt-2">🔍 Utilise YOLOv8 pour détecter chats, chiens, chevaux, etc.</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Bouton de réinitialisation */}
            <div className="mt-4 text-center">
              <button
                onClick={() => setPipelineOptions({
                  languageDetectionDuration: 30,
                  targetResolution: '360p',
                  crf: 23,
                  subtitleModel: 'tiny',
                  subtitleLanguage: 'auto',
                  enableAnimalDetection: true,
                  animalConfidenceThreshold: 0.5
                })}
                className="text-sm text-gray-400 hover:text-white transition-colors"
              >
                🔄 Réinitialiser les paramètres par défaut
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Zone de drop */}
      <div
        className={`
          relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all duration-200
          ${uploadState === 'UPLOADING'
            ? 'border-blue-400 bg-blue-50 dark:bg-blue-900/20' 
            : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500 bg-gray-50 dark:bg-gray-800/50'
          }
        `}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={() => uploadState !== 'UPLOADING' && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={acceptedFormats.join(',')}
          onChange={handleFileInputChange}
          className="hidden"
          disabled={uploadState === 'UPLOADING'}
        />
        
        {uploadState === 'IDLE' && (
          <div className="space-y-4">
            <div className="text-6xl">📹</div>
            <div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                Glissez-déposez votre vidéo ici
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                ou cliquez pour sélectionner un fichier
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                Formats supportés: MP4, AVI, MOV (max. 500 MB)
              </p>
            </div>
          </div>
        )}

        {uploadState === 'SELECTED' && selectedFile && (
          <div className="space-y-4">
            <div className="text-6xl">🎬</div>
            <div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                Fichier sélectionné
              </h3>
              <p className="text-gray-600 dark:text-gray-400 font-medium mt-2">
                {selectedFile.name}
              </p>
              <p className="text-gray-500 dark:text-gray-500 text-sm">
                {formatFileSize(selectedFile.size)}
              </p>
            </div>
          </div>
        )}

        {uploadState === 'UPLOADING' && (
          <div className="space-y-4">
            <div className="text-6xl animate-pulse">⬆️</div>
            <div>
              <h3 className="text-xl font-semibold text-blue-600 dark:text-blue-400">
                Upload en cours...
              </h3>
              <div className="mt-4 bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
                <div 
                  className="bg-blue-600 h-full transition-all duration-300 ease-out"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                {Math.round(uploadProgress)}% complété
              </p>
              <p className="text-xs text-gray-500 mt-2">
                Le traitement démarrera automatiquement après l&apos;upload
              </p>
            </div>
          </div>
        )}

        {uploadState === 'ERROR' && (
          <div className="space-y-4">
            <div className="text-6xl">❌</div>
            <div>
              <h3 className="text-xl font-semibold text-red-600 dark:text-red-400">
                Erreur
              </h3>
              <p className="text-red-500 dark:text-red-400 mt-2">
                {errorMessage}
              </p>
              <button
                onClick={handleReset}
                className="mt-4 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Réessayer
              </button>
            </div>
          </div>
        )}

        {uploadState === 'SUCCESS' && apiResponse && (
          <div className="space-y-4">
            <div className="text-6xl">✅</div>
            <div>
              <h3 className="text-xl font-semibold text-green-600 dark:text-green-400">
                Vidéo envoyée !
              </h3>
              {apiResponse.video_id && (
                <p className="text-gray-600 dark:text-gray-400 mt-2">
                  ID: <span className="font-mono text-blue-400">{apiResponse.video_id}</span>
                </p>
              )}
              <button
                onClick={handleReset}
                className="mt-4 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Uploader une autre vidéo
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Bouton d'upload */}
      {uploadState === 'SELECTED' && (
        <button
          onClick={handleUpload}
          className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 shadow-md hover:shadow-lg"
        >
          🚀 Lancer le traitement complet
        </button>
      )}

      {/* Message de succès - Traitement global */}
      {uploadState === 'SUCCESS' && globalResponse && (
        <div className={`border rounded-lg p-6 ${
          globalResponse.overall_status === 'completed' 
            ? 'bg-green-900/20 border-green-600' 
            : 'bg-red-900/20 border-red-600'
        }`}>
          {/* En-tête */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <span className="text-3xl">
                {globalResponse.overall_status === 'completed' ? '🎉' : '❌'}
              </span>
              <div>
                <h3 className="text-xl font-bold text-white">
                  {globalResponse.overall_status === 'completed' ? 'Traitement terminé !' : 'Traitement échoué'}
                </h3>
                <p className="text-sm text-gray-400">{globalResponse.message}</p>
              </div>
            </div>
            {globalResponse.total_duration && (
              <div className="text-right">
                <span className="text-xs text-gray-500">Durée totale</span>
                <p className="text-lg font-semibold text-white">{formatDuration(globalResponse.total_duration)}</p>
              </div>
            )}
          </div>

          {/* ID Vidéo */}
          <div className="bg-gray-800/50 rounded-lg p-3 mb-4">
            <span className="text-xs text-gray-500">ID Vidéo</span>
            <p className="font-mono text-sm text-blue-400">{globalResponse.video_id}</p>
          </div>

          {/* Résultats par étape */}
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-gray-400 uppercase">Résultats par étape</h4>
            
            {/* Détection de langue */}
            {globalResponse.language_detection && (
              <div className={`p-4 rounded-lg border ${
                globalResponse.language_detection.result?.skipped ? 'border-yellow-600 bg-yellow-900/10' :
                globalResponse.language_detection.status === 'completed' ? 'border-green-600 bg-green-900/10' :
                globalResponse.language_detection.status === 'failed' ? 'border-red-600 bg-red-900/10' :
                'border-gray-600 bg-gray-800/30'
              }`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={globalResponse.language_detection.result?.skipped ? 'text-yellow-400' : getStageStatus(globalResponse.language_detection.status).color}>
                      {globalResponse.language_detection.result?.skipped ? '⏭️' : getStageStatus(globalResponse.language_detection.status).icon}
                    </span>
                    <span className="font-medium text-white">🌍 Détection de langue</span>
                    {globalResponse.language_detection.result?.skipped && (
                      <span className="text-xs text-yellow-400 bg-yellow-900/30 px-2 py-0.5 rounded">Sautée</span>
                    )}
                  </div>
                  {globalResponse.language_detection.duration !== undefined && globalResponse.language_detection.duration > 0 && (
                    <span className="text-xs text-gray-500">{formatDuration(globalResponse.language_detection.duration)}</span>
                  )}
                </div>
                {globalResponse.language_detection.result && (
                  <div className="mt-2 pl-6 text-sm">
                    {globalResponse.language_detection.result.skipped ? (
                      <p className="text-yellow-300">
                        <span className="text-yellow-500">ℹ️</span>{' '}
                        {globalResponse.language_detection.result.reason === 'no_audio_track' 
                          ? 'Vidéo sans piste audio - détection de langue non applicable'
                          : globalResponse.language_detection.result.language_name || 'Étape sautée'}
                      </p>
                    ) : (
                      <>
                        <p className="text-gray-300">
                          <span className="text-gray-500">Langue:</span>{' '}
                          <span className="font-medium">{globalResponse.language_detection.result.language_name || globalResponse.language_detection.result.detected_language}</span>
                        </p>
                        {globalResponse.language_detection.result.confidence !== undefined && globalResponse.language_detection.result.confidence !== null && globalResponse.language_detection.result.confidence > 0 && (
                          <p className="text-gray-300">
                            <span className="text-gray-500">Confiance:</span>{' '}
                            <span className="font-medium">{(globalResponse.language_detection.result.confidence * 100).toFixed(1)}%</span>
                          </p>
                        )}
                      </>
                    )}
                  </div>
                )}
                {globalResponse.language_detection.error_message && (
                  <p className="mt-2 pl-6 text-sm text-red-400">{globalResponse.language_detection.error_message}</p>
                )}
              </div>
            )}

            {/* Compression */}
            {globalResponse.compression && (
              <div className={`p-4 rounded-lg border ${
                globalResponse.compression.status === 'completed' ? 'border-green-600 bg-green-900/10' :
                globalResponse.compression.status === 'failed' ? 'border-red-600 bg-red-900/10' :
                'border-gray-600 bg-gray-800/30'
              }`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={getStageStatus(globalResponse.compression.status).color}>
                      {getStageStatus(globalResponse.compression.status).icon}
                    </span>
                    <span className="font-medium text-white">📐 Compression vidéo</span>
                  </div>
                  {globalResponse.compression.duration && (
                    <span className="text-xs text-gray-500">{formatDuration(globalResponse.compression.duration)}</span>
                  )}
                </div>
                {globalResponse.compression.result && (
                  <div className="mt-2 pl-6 text-sm">
                    <p className="text-gray-300">
                      <span className="text-gray-500">Résolution:</span>{' '}
                      <span className="font-medium">{globalResponse.compression.result.resolution}</span>
                    </p>
                  </div>
                )}
                {globalResponse.compression.error_message && (
                  <p className="mt-2 pl-6 text-sm text-red-400">{globalResponse.compression.error_message}</p>
                )}
              </div>
            )}

            {/* Sous-titres */}
            {globalResponse.subtitle_generation && (
              <div className={`p-4 rounded-lg border ${
                globalResponse.subtitle_generation.result?.skipped ? 'border-yellow-600 bg-yellow-900/10' :
                globalResponse.subtitle_generation.status === 'completed' ? 'border-green-600 bg-green-900/10' :
                globalResponse.subtitle_generation.status === 'failed' ? 'border-red-600 bg-red-900/10' :
                'border-gray-600 bg-gray-800/30'
              }`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={globalResponse.subtitle_generation.result?.skipped ? 'text-yellow-400' : getStageStatus(globalResponse.subtitle_generation.status).color}>
                      {globalResponse.subtitle_generation.result?.skipped ? '⏭️' : getStageStatus(globalResponse.subtitle_generation.status).icon}
                    </span>
                    <span className="font-medium text-white">📝 Génération sous-titres</span>
                    {globalResponse.subtitle_generation.result?.skipped && (
                      <span className="text-xs text-yellow-400 bg-yellow-900/30 px-2 py-0.5 rounded">Sautée</span>
                    )}
                  </div>
                  {globalResponse.subtitle_generation.duration !== undefined && globalResponse.subtitle_generation.duration > 0 && (
                    <span className="text-xs text-gray-500">{formatDuration(globalResponse.subtitle_generation.duration)}</span>
                  )}
                </div>
                {globalResponse.subtitle_generation.result && (
                  <div className="mt-2 pl-6 text-sm">
                    {globalResponse.subtitle_generation.result.skipped ? (
                      <p className="text-yellow-300">
                        <span className="text-yellow-500">ℹ️</span>{' '}
                        {globalResponse.subtitle_generation.result.reason === 'no_audio_track' 
                          ? 'Vidéo sans piste audio - génération de sous-titres non applicable'
                          : globalResponse.subtitle_generation.result.subtitle_text_preview || 'Étape sautée'}
                      </p>
                    ) : (
                      <>
                        <p className="text-gray-300">
                          <span className="text-gray-500">Modèle:</span>{' '}
                          <span className="font-medium">{globalResponse.subtitle_generation.result.model_name}</span>
                        </p>
                        <p className="text-gray-300">
                          <span className="text-gray-500">Langue:</span>{' '}
                          <span className="font-medium">{globalResponse.subtitle_generation.result.language}</span>
                        </p>
                        {globalResponse.subtitle_generation.result.subtitle_text && (
                          <div className="mt-2">
                            <span className="text-gray-500">Aperçu:</span>
                            <p className="mt-1 text-xs text-gray-400 bg-gray-800 p-2 rounded max-h-20 overflow-y-auto">
                              {globalResponse.subtitle_generation.result.subtitle_text}
                            </p>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                )}
                {globalResponse.subtitle_generation.error_message && (
                  <p className="mt-2 pl-6 text-sm text-red-400">{globalResponse.subtitle_generation.error_message}</p>
                )}
              </div>
            )}

            {/* Détection d'animaux */}
            {globalResponse.animal_detection && (
              <div className={`p-4 rounded-lg border ${
                globalResponse.animal_detection.status === 'completed' ? 'border-green-600 bg-green-900/10' :
                globalResponse.animal_detection.status === 'failed' ? 'border-red-600 bg-red-900/10' :
                'border-gray-600 bg-gray-800/30'
              }`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={getStageStatus(globalResponse.animal_detection.status).color}>
                      {getStageStatus(globalResponse.animal_detection.status).icon}
                    </span>
                    <span className="font-medium text-white">🐾 Détection d&apos;animaux</span>
                  </div>
                  {globalResponse.animal_detection.duration && (
                    <span className="text-xs text-gray-500">{formatDuration(globalResponse.animal_detection.duration)}</span>
                  )}
                </div>
                {globalResponse.animal_detection.result && (
                  <div className="mt-2 pl-6 text-sm">
                    {globalResponse.animal_detection.result.video_info && (
                      <p className="text-gray-300">
                        <span className="text-gray-500">Frames analysées:</span>{' '}
                        <span className="font-medium">{globalResponse.animal_detection.result.video_info.processed_frames} / {globalResponse.animal_detection.result.video_info.total_frames}</span>
                      </p>
                    )}
                    {globalResponse.animal_detection.result.detection_summary && (
                      <>
                        <p className="text-gray-300">
                          <span className="text-gray-500">Total détections:</span>{' '}
                          <span className="font-medium">{globalResponse.animal_detection.result.detection_summary.total_detections}</span>
                        </p>
                        {globalResponse.animal_detection.result.detection_summary.animals_detected && 
                         Object.keys(globalResponse.animal_detection.result.detection_summary.animals_detected).length > 0 && (
                          <div className="mt-2">
                            <span className="text-gray-500">Animaux détectés:</span>
                            <div className="flex flex-wrap gap-2 mt-1">
                              {Object.entries(globalResponse.animal_detection.result.detection_summary.animals_detected).map(([animal, count]) => (
                                <span key={animal} className="bg-orange-900/50 text-orange-300 px-2 py-1 rounded text-xs">
                                  {animal}: {count}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                )}
                {globalResponse.animal_detection.error_message && (
                  <p className="mt-2 pl-6 text-sm text-red-400">{globalResponse.animal_detection.error_message}</p>
                )}
              </div>
            )}

            {/* Agrégation */}
            {globalResponse.aggregation && (
              <div className={`p-4 rounded-lg border ${
                globalResponse.aggregation.status === 'completed' ? 'border-green-600 bg-green-900/10' :
                globalResponse.aggregation.status === 'failed' ? 'border-red-600 bg-red-900/10' :
                'border-gray-600 bg-gray-800/30'
              }`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={getStageStatus(globalResponse.aggregation.status).color}>
                      {getStageStatus(globalResponse.aggregation.status).icon}
                    </span>
                    <span className="font-medium text-white">🎬 Agrégation vidéo</span>
                    {globalResponse.aggregation.result?.no_audio && (
                      <span className="text-xs text-yellow-400 bg-yellow-900/30 px-2 py-0.5 rounded">Sans sous-titres</span>
                    )}
                  </div>
                  {globalResponse.aggregation.duration && (
                    <span className="text-xs text-gray-500">{formatDuration(globalResponse.aggregation.duration)}</span>
                  )}
                </div>
                {globalResponse.aggregation.result && (
                  <div className="mt-2 pl-6 text-sm">
                    {globalResponse.aggregation.result.no_audio && (
                      <p className="text-yellow-300 mb-2">
                        <span className="text-yellow-500">ℹ️</span>{' '}
                        Vidéo traitée sans sous-titres (pas de piste audio détectée)
                      </p>
                    )}
                    {globalResponse.aggregation.result.streaming_url && (
                      <p className="text-gray-300">
                        <span className="text-gray-500">Vidéo finale:</span>{' '}
                        <a 
                          href={globalResponse.aggregation.result.streaming_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-blue-400 hover:text-blue-300 underline"
                        >
                          🎥 {globalResponse.aggregation.result.has_subtitles ? 'Voir la vidéo avec sous-titres' : 'Voir la vidéo'}
                        </a>
                      </p>
                    )}
                    {globalResponse.aggregation.result.metadata && (
                      <div className="mt-2 space-y-1">
                        {globalResponse.aggregation.result.metadata.resolution && (
                          <p className="text-gray-300">
                            <span className="text-gray-500">Résolution:</span>{' '}
                            <span className="font-medium">{globalResponse.aggregation.result.metadata.resolution}</span>
                          </p>
                        )}
                        {globalResponse.aggregation.result.metadata.duration && (
                          <p className="text-gray-300">
                            <span className="text-gray-500">Durée:</span>{' '}
                            <span className="font-medium">{formatDuration(globalResponse.aggregation.result.metadata.duration)}</span>
                          </p>
                        )}
                        {globalResponse.aggregation.result.metadata.file_size && (
                          <p className="text-gray-300">
                            <span className="text-gray-500">Taille:</span>{' '}
                            <span className="font-medium">{formatFileSize(globalResponse.aggregation.result.metadata.file_size)}</span>
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                )}
                {globalResponse.aggregation.error_message && (
                  <p className="mt-2 pl-6 text-sm text-red-400">{globalResponse.aggregation.error_message}</p>
                )}
              </div>
            )}

            {/* Lien vers la vidéo finale */}
            {globalResponse.final_streaming_url && (
              <div className="p-4 rounded-lg border border-blue-500 bg-blue-900/20">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">🎉</span>
                    <span className="font-medium text-white">Vidéo finale prête !</span>
                  </div>
                </div>
                <div className="mt-3 flex gap-3">
                  <a 
                    href={globalResponse.final_streaming_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium py-2 px-4 rounded-lg text-center transition-all duration-200"
                  >
                    ▶️ {globalResponse.aggregation?.result?.has_subtitles !== false ? 'Regarder la vidéo avec sous-titres' : 'Regarder la vidéo'}
                  </a>
                </div>
              </div>
            )}
          </div>

          {/* Statistiques */}
          <div className="mt-4 pt-4 border-t border-gray-700 flex justify-between items-center">
            <div className="flex gap-4 text-sm">
              <span className="text-green-400">✅ {globalResponse.success_count} réussi(s)</span>
              {globalResponse.failure_count > 0 && (
                <span className="text-red-400">❌ {globalResponse.failure_count} échoué(s)</span>
              )}
            </div>
            <button
              onClick={handleReset}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200"
            >
              🔄 Nouveau traitement
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

// Composant VideoList - Affiche les vidéos traitées
function VideoList({ videos, onRefresh }: { videos: VideoMetadata[], onRefresh: () => void }) {
  const [selectedVideo, setSelectedVideo] = useState<string | null>(null)

  // L'URL de streaming provient désormais du main-app
  const getStreamingUrl = (videoId: string): string => {
    return `${API_STREAMING_URL}${videoId}`
  }

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

  const getStatusBadge = (status: VideoStatus) => {
    const badges = {
      uploaded: { color: 'bg-blue-500', icon: '📤', label: 'Uploadée' },
      processing: { color: 'bg-yellow-500', icon: '⚙️', label: 'En traitement' },
      completed: { color: 'bg-green-500', icon: '✅', label: 'Terminée' },
      failed: { color: 'bg-red-500', icon: '❌', label: 'Échouée' }
    }
    const badge = badges[status] || badges.uploaded
    
    return (
      <span className={`${badge.color} text-white px-3 py-1 rounded-full text-xs font-medium inline-flex items-center gap-1`}>
        <span>{badge.icon}</span>
        <span>{badge.label}</span>
      </span>
    )
  }

  const completedVideos = videos.filter(v => v.status === 'completed')

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <span>🎥</span>
          <span>Vidéos traitées ({completedVideos.length})</span>
        </h2>
        {/* <button
          onClick={onRefresh}
          className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors duration-200 flex items-center gap-2"
        >
          <span>🔄</span>
          <span>Actualiser</span>
        </button> */}
      </div>

      {completedVideos.length === 0 ? (
        <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-8 text-center">
          <div className="text-6xl mb-4">📁</div>
          <p className="text-gray-400">Aucune vidéo traitée pour le moment</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {completedVideos.map((video) => (
            <div
              key={video.video_id}
              className={`bg-gray-800/70 border rounded-lg p-4 transition-all duration-200 cursor-pointer hover:bg-gray-800 ${
                selectedVideo === video.video_id ? 'border-blue-500 ring-2 ring-blue-500/50' : 'border-gray-700'
              }`}
              onClick={() => setSelectedVideo(selectedVideo === video.video_id ? null : video.video_id)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-white truncate">
                      {video.original_filename}
                    </h3>
                    {getStatusBadge(video.status)}
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm text-gray-400">
                    <div className="flex items-center gap-2">
                      <span className='text-gray-400'>📊 Taille :</span>
                      <span>{formatFileSize(video.file_size)}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className='text-gray-400'>🕒 Lancé le :</span>
                      <span>{formatDate(video.upload_time)}</span>
                    </div>
                    {/* <div className="flex items-center gap-2">
                      <span>🆔</span>
                      <span className="truncate">{video.video_id}</span>
                    </div> */}
                    {/* <div className="flex items-center gap-2">
                      <span>📝</span>
                      <span>{video.content_type}</span>
                    </div> */}
                  </div>
                  {/* Bouton de détails */}
                  <div className="mt-3">
                    <a
                      href={`/video/${video.video_id}`}
                      className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                      onClick={(e) => {
                        e.stopPropagation()
                      }}
                    >
                      🔍 Consulter le résultat
                    </a>
                  </div>
                </div>
                <div className="text-2xl ml-4">
                  {selectedVideo === video.video_id ? '🔼' : '🔽'}
                </div>
              </div>

              {/* Affichage du lecteur vidéo uniquement si sélectionné */}
              {selectedVideo === video.video_id && (
                <div className="mt-4 pt-4 border-t border-gray-700">
                  <video
                    controls
                    className="w-full rounded-lg bg-black"
                    src={getStreamingUrl(video.video_id)}
                  >
                    Votre navigateur ne supporte pas la lecture vidéo.
                  </video>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// Composant ProcessingVideos - Affiche les vidéos en traitement avec progression
function ProcessingVideos({ videos, onRefresh }: { videos: VideoMetadata[], onRefresh: () => void }) {
  const formatDate = (dateStr: string): string => {
    return new Date(dateStr).toLocaleString('fr-FR')
  }

  // Définition des étapes avec leurs icônes et labels
  const stages = [
    { id: 'language_detection', icon: '🌍', label: 'Détection langue' },
    { id: 'compression', icon: '📐', label: 'Compression' },
    { id: 'subtitle_generation', icon: '📝', label: 'Sous-titres' },
    { id: 'animal_detection', icon: '🐾', label: 'Animaux' },
    { id: 'aggregation', icon: '🎬', label: 'Agrégation' }
  ]

  // Obtenir le statut d'une étape pour une vidéo
  const getStageStatus = (video: VideoMetadata, stageId: string): 'pending' | 'processing' | 'completed' | 'failed' => {
    if (video.stages_completed?.includes(stageId)) return 'completed'
    if (video.stages_failed?.includes(stageId)) return 'failed'
    if (video.current_stage === stageId) return 'processing'
    return 'pending'
  }

  // Calculer la progression en pourcentage
  const getProgress = (video: VideoMetadata): number => {
    const completed = video.stages_completed?.length || 0
    const failed = video.stages_failed?.length || 0
    const total = 5 // 5 étapes possibles maintenant
    return Math.round(((completed + failed) / total) * 100)
  }

  const processingVideos = videos.filter(v => v.status === 'processing')

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <span>⚙️</span>
          <span>Traitement en cours ({processingVideos.length})</span>
        </h2>
        {/* <button
          onClick={onRefresh}
          className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors duration-200 flex items-center gap-2"
        >
          <span>🔄</span>
          <span>Actualiser</span>
        </button> */}
      </div>

      {processingVideos.length === 0 ? (
        <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-8 text-center">
          <div className="text-6xl mb-4">✨</div>
          <p className="text-gray-400">Aucune vidéo en cours de traitement</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {processingVideos.map((video) => (
            <div
              key={video.video_id}
              className="bg-linear-to-r from-yellow-900/20 to-orange-900/20 border border-yellow-600/50 rounded-lg p-4"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  {/* En-tête avec nom du fichier */}
                  <div className="flex items-center gap-3 mb-3">
                    <div className="animate-spin text-2xl">⚙️</div>
                    <h3 className="text-lg font-semibold text-white truncate">
                      {video.original_filename}
                    </h3>
                  </div>
                  
                  {/* Informations de base */}
                  <div className="space-y-2 text-sm text-gray-300 mb-4">
                    <div className="flex items-center gap-2">
                      <span>🆔</span>
                      <span className="truncate font-mono text-xs">{video.video_id}</span>
                    </div>
                    {(video.processing_start_time || video.processing_time) && (
                      <div className="flex items-center gap-2">
                        <span>🕒</span>
                        <span>Démarré: {formatDate(video.processing_start_time || video.processing_time || '')}</span>
                      </div>
                    )}
                  </div>

                  {/* Progression des étapes */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-400">Progression</span>
                      <span className="text-yellow-400 font-semibold">{getProgress(video)}%</span>
                    </div>
                    
                    {/* Barre de progression */}
                    <div className="bg-gray-700 rounded-full h-2 overflow-hidden">
                      <div 
                        className="bg-linear-to-r from-yellow-500 to-orange-500 h-full transition-all duration-500"
                        style={{ width: `${getProgress(video)}%` }}
                      />
                    </div>

                    {/* Étapes détaillées */}
                    <div className="flex justify-between gap-2 mt-3">
                      {stages.map((stage) => {
                        const stageStatus = getStageStatus(video, stage.id)
                        return (
                          <div 
                            key={stage.id}
                            className={`flex-1 p-2 rounded-lg text-center transition-all ${
                              stageStatus === 'completed' ? 'bg-green-900/30 border border-green-600/50' :
                              stageStatus === 'failed' ? 'bg-red-900/30 border border-red-600/50' :
                              stageStatus === 'processing' ? 'bg-yellow-900/30 border border-yellow-600/50 animate-pulse' :
                              'bg-gray-800/50 border border-gray-700'
                            }`}
                          >
                            <div className={`text-lg mb-1 ${stageStatus === 'processing' ? 'animate-bounce' : ''}`}>
                              {stageStatus === 'completed' ? '✅' :
                               stageStatus === 'failed' ? '❌' :
                               stageStatus === 'processing' ? '🔄' :
                               stage.icon}
                            </div>
                            <div className={`text-xs font-medium ${
                              stageStatus === 'completed' ? 'text-green-400' :
                              stageStatus === 'failed' ? 'text-red-400' :
                              stageStatus === 'processing' ? 'text-yellow-400' :
                              'text-gray-500'
                            }`}>
                              {stage.label}
                            </div>
                            <div className="text-xs mt-1">
                              {stageStatus === 'completed' ? '✓ Terminé' :
                               stageStatus === 'failed' ? '✗ Échoué' :
                               stageStatus === 'processing' ? '⏳ En cours...' :
                               '○ En attente'}
                            </div>
                          </div>
                        )
                      })}
                    </div>

                    {/* Étape actuelle */}
                    {video.current_stage && video.current_stage !== 'completed' && video.current_stage !== 'initializing' && video.current_stage !== 'failed' && (
                      <div className="mt-2 text-center">
                        <span className="text-xs text-yellow-400 bg-yellow-900/30 px-3 py-1 rounded-full">
                          🔄 {stages.find(s => s.id === video.current_stage)?.label || video.current_stage} en cours...
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// Composant FailedVideos - Affiche les vidéos en échec
function FailedVideos({ videos, onRefresh }: { videos: VideoMetadata[], onRefresh: () => void }) {
  const formatDate = (dateStr: string): string => {
    return new Date(dateStr).toLocaleString('fr-FR')
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const failedVideos = videos.filter(v => v.status === 'failed')

  if (failedVideos.length === 0) return null

  return (
    <div className="space-y-4 mt-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-red-400 flex items-center gap-2">
          <span>❌</span>
          <span>Échecs ({failedVideos.length})</span>
        </h2>
        {/* <button
          onClick={onRefresh}
          className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors duration-200 flex items-center gap-2"
        >
          <span>🔄</span>
          <span>Actualiser</span>
        </button> */}
      </div>

      <div className="grid gap-4">
        {failedVideos.map((video) => (
          <div
            key={video.video_id}
            className="bg-red-900/20 border border-red-600/50 rounded-lg p-4"
          >
            <div className="flex items-start gap-3">
              <span className="text-2xl">❌</span>
              <div className="flex-1 min-w-0">
                <h3 className="text-lg font-semibold text-white truncate">
                  {video.original_filename}
                </h3>
                <div className="grid grid-cols-2 gap-2 text-sm text-gray-400 mt-2">
                  <div className="flex items-center gap-2">
                    <span>📊</span>
                    <span>{formatFileSize(video.file_size)}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span>🕒</span>
                    <span>{formatDate(video.upload_time)}</span>
                  </div>
                </div>
                {video.stages_failed && video.stages_failed.length > 0 && (
                  <div className="mt-2 text-sm text-red-400">
                    Étape échouée: {video.stages_failed.join(', ')}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// Composant principal de la page
export default function Home() {
  const [videos, setVideos] = useState<VideoMetadata[]>([])
  const [isLoading, setIsLoading] = useState(true)

  const fetchVideos = async () => {
    try {
      const response = await fetch(API_LIST_URL)
      if (response.ok) {
        const data = await response.json()
        setVideos(data)
      }
    } catch (error) {
      console.error('Erreur lors du chargement des vidéos:', error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchVideos()
    // Actualiser toutes les 5 secondes
    const interval = setInterval(fetchVideos, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <header className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4 bg-linear-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            Pipeline hybride de traitement vidéo (VidP)
          </h1>
          <p className="text-gray-300 text-lg max-w-2xl mx-auto">
            Interface de soumission pour le traitement initial de vos vidéos. 
            Téléchargez vos fichiers vidéo pour commencer le processus d&apos;analyse automatique.
          </p>
        </header>

        {/* Contenu principal */}
        <main>
          {/* Upload */}
          <div className='w-full mb-12'>
            <VideoUploader onUploadSuccess={fetchVideos} />
          </div>

          <div className='grid lg:grid-cols-2 gap-8'>
            {/* Colonne gauche - Traitement */}
            <div className="space-y-8">
              <ProcessingVideos videos={videos} onRefresh={fetchVideos} />
              <FailedVideos videos={videos} onRefresh={fetchVideos} />
            </div>

            {/* Colonne droite - Liste des vidéos */}
            <div>
              {isLoading ? (
                <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-8 text-center">
                  <div className="text-6xl mb-4 animate-pulse">⏳</div>
                  <p className="text-gray-400">Chargement des vidéos...</p>
                </div>
              ) : (
                <VideoList videos={videos} onRefresh={fetchVideos} />
              )}
            </div>
          </div>
        </main>

        {/* Footer */}
        <footer className="text-center mt-16 pt-8 border-t border-gray-700">
          <p className="text-gray-400">
            INF5141 Cloud Computing - Projet VidP &nbsp;|&nbsp; Réalisé par HN-DS-CIN 5 &copy; 2025
          </p>
        </footer>
      </div>
    </div>
  )
}
