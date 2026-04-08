import { useRef, useEffect, useCallback } from 'react';

export default function WebcamDetector({
  videoRef,
  isActive,
  detections,
  onStart,
  onStop,
}) {
  const canvasRef = useRef(null);

  // Draw bounding boxes on canvas overlay
  const drawDetections = useCallback(() => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    if (!canvas || !video) return;

    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!detections || detections.length === 0) return;

    detections.forEach((det) => {
      const [x1, y1, x2, y2] = det.bbox;
      const w = x2 - x1;
      const h = y2 - y1;

      // Box
      ctx.strokeStyle = '#22d3ee';
      ctx.lineWidth = 2;
      ctx.shadowColor = 'rgba(34, 211, 238, 0.5)';
      ctx.shadowBlur = 8;
      ctx.strokeRect(x1, y1, w, h);
      ctx.shadowBlur = 0;

      // Label background
      const label = `${det.ingredient || det.yolo_class} ${Math.round(det.confidence * 100)}%`;
      ctx.font = '600 13px Inter, sans-serif';
      const textW = ctx.measureText(label).width;
      const labelH = 22;
      const labelY = y1 > labelH + 4 ? y1 - labelH - 4 : y1;

      ctx.fillStyle = 'rgba(6, 182, 212, 0.85)';
      ctx.beginPath();
      ctx.roundRect(x1, labelY, textW + 12, labelH, 4);
      ctx.fill();

      // Label text
      ctx.fillStyle = '#fff';
      ctx.fillText(label, x1 + 6, labelY + 15);
    });
  }, [detections, videoRef]);

  useEffect(() => {
    drawDetections();
  }, [drawDetections]);

  return (
    <section className="webcam-section">
      <div className="app-container">
        <div className="section-title">
          <span className="icon">📸</span>
          <h2>Live Detection</h2>
        </div>

        <div className="webcam-wrapper">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            style={{ display: isActive ? 'block' : 'none' }}
          />
          <canvas ref={canvasRef} />

          {!isActive && (
            <div className="webcam-placeholder">
              <span className="icon">📷</span>
              <p>Point your camera at ingredients</p>
              <button className="cam-btn" onClick={onStart}>
                Start Camera
              </button>
            </div>
          )}
        </div>

        {isActive && (
          <div style={{ textAlign: 'center', marginTop: '16px' }}>
            <button className="cam-btn stop" onClick={onStop}>
              Stop Camera
            </button>
          </div>
        )}
      </div>
    </section>
  );
}
