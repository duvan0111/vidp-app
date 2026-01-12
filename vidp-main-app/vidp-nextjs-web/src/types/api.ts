// Types et interfaces pour l'application VidP Frontend

/**
 * États possibles du processus d'upload
 */
export type UploadState = 'IDLE' | 'SELECTED' | 'UPLOADING' | 'SUCCESS' | 'ERROR'

/**
 * Interface pour la réponse de l'API FastAPI
 */
export interface ApiResponse {
  /** ID unique de la vidéo générée par le backend */
  video_id?: string
  /** Message de confirmation ou d'information */
  message?: string
  /** Détails de l'erreur en cas d'échec */
  detail?: string
}

/**
 * Interface pour les informations de fichier
 */
export interface FileInfo {
  /** Nom du fichier */
  name: string
  /** Taille en bytes */
  size: number
  /** Type MIME */
  type: string
  /** Date de dernière modification */
  lastModified: number
}

/**
 * Configuration de l'application
 */
export interface AppConfig {
  /** URL de l'API backend */
  apiUrl: string
  /** Taille maximale des fichiers en bytes */
  maxFileSize: number
  /** Formats vidéo acceptés (types MIME) */
  acceptedFormats: string[]
  /** Timeout des requêtes en ms */
  requestTimeout: number
}

/**
 * Réponse d'erreur standardisée
 */
export interface ErrorResponse {
  /** Code d'erreur HTTP */
  status: number
  /** Message d'erreur principal */
  message: string
  /** Détails supplémentaires */
  detail?: string
  /** Timestamp de l'erreur */
  timestamp: string
}

/**
 * Événement de progression d'upload
 */
export interface UploadProgressEvent {
  /** Bytes envoyés */
  loaded: number
  /** Total à envoyer */
  total: number
  /** Pourcentage (0-100) */
  percentage: number
}

/**
 * Constantes de l'application
 */
export const APP_CONSTANTS = {
  /** URL par défaut de l'API */
  DEFAULT_API_URL: 'http://localhost:8000/api/v1/videos/upload',
  
  /** Taille maximale des fichiers (500 MB) */
  MAX_FILE_SIZE: 500 * 1024 * 1024,
  
  /** Formats vidéo supportés */
  ACCEPTED_FORMATS: [
    'video/mp4',
    'video/avi', 
    'video/mov',
    'video/quicktime',
    'video/x-msvideo'
  ] as string[],
  
  /** Extensions de fichier supportées */
  ACCEPTED_EXTENSIONS: ['mp4', 'avi', 'mov'],
  
  /** Timeout par défaut (30 secondes) */
  DEFAULT_TIMEOUT: 30000,
  
  /** Messages d'erreur */
  ERROR_MESSAGES: {
    INVALID_FORMAT: 'Format de fichier non supporté. Veuillez sélectionner un fichier MP4, AVI ou MOV.',
    FILE_TOO_LARGE: 'La taille du fichier dépasse 500 MB. Veuillez sélectionner un fichier plus petit.',
    NETWORK_ERROR: 'Erreur réseau lors de l\'upload',
    PARSE_ERROR: 'Erreur lors du parsing de la réponse',
    UNKNOWN_ERROR: 'Erreur inconnue lors du traitement'
  }
} as const

/**
 * Utilitaires pour la validation des fichiers
 */
export class FileValidator {
  /**
   * Valide un fichier selon les critères de l'application
   */
  static validate(file: File): string | null {
    const acceptedFormats: string[] = APP_CONSTANTS.ACCEPTED_FORMATS;
    if (!acceptedFormats.includes(file.type)) {
      return APP_CONSTANTS.ERROR_MESSAGES.INVALID_FORMAT
    }
    
    if (file.size > APP_CONSTANTS.MAX_FILE_SIZE) {
      return APP_CONSTANTS.ERROR_MESSAGES.FILE_TOO_LARGE
    }
    
    return null
  }
  
  /**
   * Formate la taille d'un fichier en unités lisibles
   */
  static formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes'
    
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }
}
