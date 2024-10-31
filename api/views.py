from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from django.conf import settings
import pandas as pd
import os
from typing import Dict, Any, Optional
import logging
from .models import DataFile  # Add missing import
from .serializers import DataFileSerializer  # Add missing import

logger = logging.getLogger(__name__)

class DataFileViewSet(viewsets.ModelViewSet):
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = ['.csv']
    MAX_COLUMNS = 100
    MAX_ROWS = 1000000
    SAMPLE_SIZE = 5

    queryset = DataFile.objects.all()
    serializer_class = DataFileSerializer

    def validate_file(self, file_obj) -> tuple[bool, Optional[str]]:
        """Validate uploaded file specifications."""
        try:
            # Check if file exists
            if not file_obj:
                return False, "No file provided"

            # Check file extension
            file_extension = os.path.splitext(file_obj.name)[1].lower()
            if file_extension not in self.ALLOWED_EXTENSIONS:
                return False, f"Invalid file type. Allowed types: {', '.join(self.ALLOWED_EXTENSIONS)}"

            # Check file size
            if file_obj.size > self.MAX_FILE_SIZE:
                return False, f"File size exceeds {self.MAX_FILE_SIZE // (1024*1024)}MB limit"

            return True, None

        except Exception as e:
            logger.error(f"File validation error: {str(e)}")
            return False, "File validation failed"

    def validate_dataframe(self, df: pd.DataFrame) -> tuple[bool, Optional[str]]:
        """Validate DataFrame specifications."""
        try:
            if df.empty:
                return False, "The file is empty"

            if len(df.columns) > self.MAX_COLUMNS:
                return False, f"Too many columns. Maximum allowed: {self.MAX_COLUMNS}"

            if len(df) > self.MAX_ROWS:
                return False, f"Too many rows. Maximum allowed: {self.MAX_ROWS}"

            # Check for duplicate column names
            if df.columns.duplicated().any():
                return False, "Duplicate column names found"

            # Check for minimum required columns (if any)
            # required_columns = ['column1', 'column2']
            # if not all(col in df.columns for col in required_columns):
            #     return False, f"Missing required columns: {required_columns}"

            return True, None

        except Exception as e:
            logger.error(f"DataFrame validation error: {str(e)}")
            return False, "DataFrame validation failed"

    def infer_and_convert_types(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Infer and convert column data types with error handling."""
        try:
            type_info = {}
            
            for column in df.columns:
                try:
                    # Get sample values with proper error handling
                    sample_values = df[column].dropna().head(self.SAMPLE_SIZE).tolist()
                    
                    # Numeric type inference
                    try:
                        numeric_series = pd.to_numeric(df[column], errors='raise')
                        if all(float(x).is_integer() for x in df[column].dropna()):
                            type_info[column] = {
                                'type': 'integer',
                                'sample_values': sample_values,
                                'original_type': str(df[column].dtype),
                                'null_count': df[column].isna().sum(),
                                'unique_count': df[column].nunique()
                            }
                        else:
                            type_info[column] = {
                                'type': 'float',
                                'sample_values': sample_values,
                                'original_type': str(df[column].dtype),
                                'null_count': df[column].isna().sum(),
                                'unique_count': df[column].nunique()
                            }
                        continue
                    except (ValueError, TypeError):
                        pass

                    # DateTime type inference
                    try:
                        pd.to_datetime(df[column], errors='raise')
                        type_info[column] = {
                            'type': 'datetime',
                            'sample_values': sample_values,
                            'original_type': str(df[column].dtype),
                            'null_count': df[column].isna().sum(),
                            'unique_count': df[column].nunique()
                        }
                        continue
                    except (ValueError, TypeError):
                        pass

                    # Categorical/Text type inference
                    unique_ratio = len(df[column].unique()) / len(df[column])
                    if unique_ratio < 0.5:
                        type_info[column] = {
                            'type': 'category',
                            'sample_values': sample_values,
                            'original_type': str(df[column].dtype),
                            'null_count': df[column].isna().sum(),
                            'unique_count': df[column].nunique(),
                            'unique_ratio': round(unique_ratio, 2)
                        }
                    else:
                        type_info[column] = {
                            'type': 'text',
                            'sample_values': sample_values,
                            'original_type': str(df[column].dtype),
                            'null_count': df[column].isna().sum(),
                            'unique_count': df[column].nunique(),
                            'unique_ratio': round(unique_ratio, 2)
                        }

                except Exception as column_error:
                    logger.error(f"Error processing column {column}: {str(column_error)}")
                    type_info[column] = {
                        'type': 'error',
                        'error': str(column_error)
                    }

            return type_info

        except Exception as e:
            logger.error(f"Type inference error: {str(e)}")
            raise ValueError(f"Failed to infer column types: {str(e)}")

    @action(detail=True, methods=['POST'])
    def process_file(self, request, pk=None):
        """Process uploaded file and return analysis results."""
        try:
            file_obj = self.get_object()
            
            # Validate file existence
            if not file_obj.file:
                return Response(
                    {'error': 'File not found on server'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Validate file
            is_valid, error_message = self.validate_file(file_obj.file)
            if not is_valid:
                return Response(
                    {'error': error_message},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                # Read CSV with various encodings
                for encoding in ['utf-8', 'latin1', 'iso-8859-1']:
                    try:
                        df = pd.read_csv(file_obj.file.path, encoding=encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    return Response(
                        {'error': 'Unable to decode file with supported encodings'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Validate DataFrame
                is_valid, error_message = self.validate_dataframe(df)
                if not is_valid:
                    return Response(
                        {'error': error_message},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Process file and infer types
                type_info = self.infer_and_convert_types(df)

                # Prepare response
                response_data = {
                    'status': 'success',
                    'file_name': file_obj.file.name,
                    'file_size': file_obj.file.size,
                    'total_rows': len(df),
                    'total_columns': len(df.columns),
                    'column_types': type_info,
                    'columns': list(df.columns),
                    'sample_data': df.head(self.SAMPLE_SIZE).to_dict(orient='records')
                }

                return Response(response_data)

            except pd.errors.EmptyDataError:
                return Response(
                    {'error': 'The file is empty'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except pd.errors.ParserError:
                return Response(
                    {'error': 'Invalid CSV format'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except DataFile.DoesNotExist:
            return Response(
                {'error': 'File not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"File processing error: {str(e)}")
            return Response(
                {'error': f'An unexpected error occurred: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )