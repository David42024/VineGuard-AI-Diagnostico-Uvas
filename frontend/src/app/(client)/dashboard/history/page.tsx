"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Search,
  Eye,
  Trash2,
  Download,
  RotateCcw,
  ChevronLeft,
  ChevronRight,
  Leaf,
} from "lucide-react";
import { formatDate, formatConfidence } from "@/lib/utils";
import { toast } from "sonner";
import { EmptyState } from "@/components/feedback/empty-state";

interface HistoryItem {
  id: number;
  filename: string;
  date: Date;
  model: string;
  prediction: string;
  confidence: number;
  health_status: "healthy" | "diseased";
}

const mockHistory: HistoryItem[] = Array.from({ length: 15 }, (_, i) => ({
  id: i + 1,
  filename: `hoja_${String(i + 1).padStart(3, "0")}.jpg`,
  date: new Date(Date.now() - 86400000 * i),
  model: ["EfficientNet", "ResNet50", "ViT"][i % 3],
  prediction: ["Sana", "Podredumbre Negra", "Esca"][i % 3],
  confidence: 0.85 + Math.random() * 0.14,
  health_status: i % 3 === 0 ? "healthy" : "diseased",
}));

const ITEMS_PER_PAGE = 6;

export default function HistoryPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [items] = useState(mockHistory);
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);

  const filtered = items.filter((h) =>
    h.filename.toLowerCase().includes(search.toLowerCase())
  );
  const totalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE);
  const paged = filtered.slice(
    (page - 1) * ITEMS_PER_PAGE,
    page * ITEMS_PER_PAGE
  );

  const handleDelete = (id: number) => {
    toast.success(`Diagnóstico #${id} eliminado`);
    setDeleteConfirm(null);
  };

  const handleRepeat = (item: HistoryItem) => {
    toast.success(`Re-analizando ${item.filename}`);
  };

  const handleDownload = (item: HistoryItem) => {
    toast.success(`Reporte de ${item.filename} descargado`);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">
          Historial de Diagnósticos
        </h2>
        <p className="text-muted-foreground">
          Consulta todos tus diagnósticos anteriores
        </p>
      </div>

      <div className="flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Buscar por archivo..."
            className="pl-10"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {paged.length === 0 ? (
        <EmptyState
          title="Sin diagnósticos"
          description="No se encontraron diagnósticos que coincidan con tu búsqueda."
          actionLabel="Ir a Nuevo Diagnóstico"
        />
      ) : (
        <>
          {/* Mobile: card view */}
          <div className="grid gap-4 md:hidden">
            {paged.map((item) => (
              <Card key={item.id}>
                <CardContent className="p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Leaf className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm font-medium">
                        {item.filename}
                      </span>
                    </div>
                    <Badge
                      variant={
                        item.health_status === "healthy"
                          ? "success"
                          : "destructive"
                      }
                    >
                      {item.prediction}
                    </Badge>
                  </div>
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>{formatDate(item.date)}</span>
                    <span>{formatConfidence(item.confidence)}</span>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" className="flex-1">
                      <Eye className="h-4 w-4 mr-1" /> Ver
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => handleRepeat(item)}
                    >
                      <RotateCcw className="h-4 w-4 mr-1" /> Repetir
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDownload(item)}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                    <Dialog
                      open={deleteConfirm === item.id}
                      onOpenChange={(open) =>
                        setDeleteConfirm(open ? item.id : null)
                      }
                    >
                      <DialogTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-destructive"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>Eliminar diagnóstico</DialogTitle>
                          <DialogDescription>
                            ¿Estás seguro de eliminar el diagnóstico de{" "}
                            {item.filename}? Esta acción no se puede deshacer.
                          </DialogDescription>
                        </DialogHeader>
                        <DialogFooter>
                          <Button
                            variant="outline"
                            onClick={() => setDeleteConfirm(null)}
                          >
                            Cancelar
                          </Button>
                          <Button
                            variant="destructive"
                            onClick={() => handleDelete(item.id)}
                          >
                            Eliminar
                          </Button>
                        </DialogFooter>
                      </DialogContent>
                    </Dialog>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Desktop: table view */}
          <Card className="hidden md:block">
            <CardHeader>
              <CardTitle className="text-lg">Historial</CardTitle>
            </CardHeader>
            <CardContent>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left font-medium text-muted-foreground p-3">Archivo</th>
                    <th className="text-left font-medium text-muted-foreground p-3">Fecha</th>
                    <th className="text-left font-medium text-muted-foreground p-3">Modelo</th>
                    <th className="text-left font-medium text-muted-foreground p-3">Predicción</th>
                    <th className="text-left font-medium text-muted-foreground p-3">Confianza</th>
                    <th className="text-right font-medium text-muted-foreground p-3">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {paged.map((item) => (
                    <tr key={item.id} className="border-b last:border-0">
                      <td className="p-3 font-medium">{item.filename}</td>
                      <td className="p-3 text-muted-foreground">
                        {formatDate(item.date)}
                      </td>
                      <td className="p-3">
                        <Badge variant="outline">{item.model}</Badge>
                      </td>
                      <td className="p-3">
                        <Badge
                          variant={
                            item.health_status === "healthy"
                              ? "success"
                              : "destructive"
                          }
                        >
                          {item.prediction}
                        </Badge>
                      </td>
                      <td className="p-3">
                        {formatConfidence(item.confidence)}
                      </td>
                      <td className="p-3 text-right">
                        <div className="flex justify-end gap-1">
                          <Button variant="ghost" size="icon">
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleRepeat(item)}
                          >
                            <RotateCcw className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDownload(item)}
                          >
                            <Download className="h-4 w-4" />
                          </Button>
                          <Dialog
                            open={deleteConfirm === item.id}
                            onOpenChange={(open) =>
                              setDeleteConfirm(open ? item.id : null)
                            }
                          >
                            <DialogTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="text-destructive"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </DialogTrigger>
                            <DialogContent>
                              <DialogHeader>
                                <DialogTitle>Eliminar diagnóstico</DialogTitle>
                                <DialogDescription>
                                  ¿Estás seguro de eliminar el diagnóstico de{" "}
                                  {item.filename}?
                                </DialogDescription>
                              </DialogHeader>
                              <DialogFooter>
                                <Button
                                  variant="outline"
                                  onClick={() => setDeleteConfirm(null)}
                                >
                                  Cancelar
                                </Button>
                                <Button
                                  variant="destructive"
                                  onClick={() => handleDelete(item.id)}
                                >
                                  Eliminar
                                </Button>
                              </DialogFooter>
                            </DialogContent>
                          </Dialog>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>

          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Mostrando {(page - 1) * ITEMS_PER_PAGE + 1}-
              {Math.min(page * ITEMS_PER_PAGE, filtered.length)} de{" "}
              {filtered.length}
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page === totalPages}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
